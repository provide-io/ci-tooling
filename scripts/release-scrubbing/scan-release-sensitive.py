#!/usr/bin/env python3
"""Scan repo history for release-sensitive content: emails, internal domains,
name variants, internal URLs, private IPs, absolute file:// URLs.

Customize PATTERNS and EMAIL_IGNORE below per project before running.
"""
from __future__ import annotations

import re
import subprocess
from collections import defaultdict

REPO = "/Volumes/data/pyv/REPONAME"

# Each regex uses non-capturing groups so re.findall returns the full match.
# Add/remove patterns to fit your release criteria.
PATTERNS = {
    "email": re.compile(rb"[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    # prior-employer / affiliation domains — tune per-person
    "nwea": re.compile(rb"(?i)nwea\.org|@nwea\b"),
    "hmhco": re.compile(rb"(?i)hmhco\.com|@hmh\b|@hmhco\b"),
    # full-name variants you don't want in public
    "tim": re.compile(rb"(?i)tim\.perkins|timothy\.perkins|timothy[_ ]perkins"),
    # private IPv4 ranges
    "private_ip": re.compile(
        rb"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
    ),
    # common internal SaaS host patterns
    "internal_url": re.compile(
        rb"https?://[a-z0-9.-]*(?:slack|atlassian|datadog|grafana|jira|confluence|newrelic)[a-z0-9.-]*\.[a-z]{2,}"
    ),
    "file_url_abs": re.compile(rb"file://+/[A-Za-z0-9_./-]+"),
}

# Emails you consider public/acceptable (substring match).
EMAIL_IGNORE = {
    b"users.noreply.github.com",
    b"example.com",
    b"example.org",
    b"localhost",
    b"test.com",
    b"code@tim.life",
    # add your project's canonical public addresses here
}


def run(args: list[str], stdin: bytes | None = None) -> bytes:
    return subprocess.run(args, cwd=REPO, input=stdin, check=False, capture_output=True).stdout


def scan(data: bytes) -> dict[str, set[bytes]]:
    hits: dict[str, set[bytes]] = defaultdict(set)
    for name, pat in PATTERNS.items():
        for m in pat.findall(data):
            if name == "email" and any(ign in m for ign in EMAIL_IGNORE):
                continue
            hits[name].add(m)
    return hits


def main() -> int:
    raw = run(["git", "rev-list", "--objects", "--all"]).decode("utf-8", "replace")
    blob_paths: dict[str, set[str]] = defaultdict(set)
    for line in raw.splitlines():
        if " " in line:
            sha, path = line.split(" ", 1)
            blob_paths[sha].add(path)

    typed = run(
        ["git", "cat-file", "--batch-check=%(objecttype) %(objectname)"],
        stdin=("\n".join(blob_paths.keys()) + "\n").encode(),
    )
    blobs = [r.split()[1] for r in typed.decode().splitlines() if r.startswith("blob ")]

    per_category: dict[str, set[bytes]] = defaultdict(set)
    per_category_path: dict[str, set[str]] = defaultdict(set)

    for sha in blobs:
        hits = scan(run(["git", "cat-file", "-p", sha]))
        for cat, matches in hits.items():
            per_category[cat] |= matches
            per_category_path[cat] |= blob_paths.get(sha, set())

    for sha in run(["git", "rev-list", "--all"]).decode().split():
        hits = scan(run(["git", "log", "--format=%B", "-n", "1", sha]))
        for cat, matches in hits.items():
            per_category[cat] |= matches
            per_category_path[cat].add(f"<commit-msg:{sha[:10]}>")

    authors = run(["git", "log", "--all", "--format=%ae%n%ce"]).decode().splitlines()
    author_emails = sorted({e for e in authors if e})

    print(f"blobs scanned: {len(blobs)}")
    print()
    print("=== committer/author emails (git metadata) ===")
    for e in author_emails:
        print(f"  {e}")
    print()
    for cat in PATTERNS:
        matches = per_category.get(cat, set())
        if not matches:
            print(f"=== {cat}: clean ===")
            continue
        print(f"=== {cat}: {len(matches)} unique ===")
        for m in sorted(matches):
            print(f"  {m.decode('utf-8', 'replace')}")
        paths = sorted(per_category_path[cat])
        print(f"  in paths: {paths[:6]}{' ...' if len(paths) > 6 else ''}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
