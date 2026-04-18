#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Scan every blob + commit message for absolute filesystem paths.

Flags content like /Users/<name>/..., /home/<name>/..., C:\\Users\\<name>\\...,
/REDACTED_TMP — path leakage that reveals usernames, directory
structure, or sibling-project names. Not secrets, but cruft that should be
kept out of history.

Usage: set REPO to the repo directory, then `python3 scan-paths.py`.
Classify results into Class A (whole path is cruft - purge via paths-from-file)
and Class B (path stays, old revs leak - scrub via filter-repo --replace-text).
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict

REPO = "/Volumes/data/pyv/REPONAME"

# Non-capturing groups so re.findall returns the full match, not sub-groups.
ABS_PATTERNS = [
    re.compile(rb"/(?:Users|home)/[a-zA-Z][a-zA-Z0-9_.-]+/[a-zA-Z0-9_./-]+"),
    re.compile(rb"[A-Z]:\\\\Users\\\\[A-Za-z0-9_.-]+\\\\[A-Za-z0-9_.\\\\-]+"),
    re.compile(rb"/private/var/folders/[a-zA-Z0-9_.-]+/[A-Za-z0-9_./-]+"),
    re.compile(rb"/var/folders/[a-zA-Z0-9_.-]+/[A-Za-z0-9_./-]+"),
]

# Generic placeholders that shouldn't count as leaks.
SKIP_IN = [
    b"/Users/Shared",
    b"/home/runner",      # github actions
    b"/home/user",        # stock docker examples
    b"/home/vscode",      # devcontainers
    b"$HOME",
]


def run(args: list[str], stdin: bytes | None = None) -> bytes:
    return subprocess.run(
        args, cwd=REPO, input=stdin, check=False, capture_output=True
    ).stdout


def scan_bytes(data: bytes) -> list[bytes]:
    hits: list[bytes] = []
    for pat in ABS_PATTERNS:
        for m in pat.findall(data):
            if any(s in m for s in SKIP_IN):
                continue
            hits.append(m)
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
    blobs = [row.split()[1] for row in typed.decode().splitlines()
             if row.startswith("blob ")]

    commits = run(["git", "rev-list", "--all"]).decode("ascii", "replace").split()

    blob_hits: dict[str, list[bytes]] = defaultdict(list)
    for sha in blobs:
        hits = scan_bytes(run(["git", "cat-file", "-p", sha]))
        if hits:
            blob_hits[sha] = hits

    commit_hits: dict[str, list[bytes]] = defaultdict(list)
    for sha in commits:
        hits = scan_bytes(run(["git", "log", "--format=%B", "-n", "1", sha]))
        if hits:
            commit_hits[sha] = hits

    print(f"scanned blobs={len(blobs)} commits={len(commits)}")
    print(f"blobs with abs-path hits: {len(blob_hits)}")
    print(f"commits with abs-path hits: {len(commit_hits)}")
    print()

    by_path: dict[str, list[str]] = defaultdict(list)
    path_at_head: dict[str, bool] = {}
    for sha, hits in blob_hits.items():
        for path in blob_paths.get(sha, {"<unknown>"}):
            for h in hits:
                by_path[path].append(h.decode("utf-8", "replace"))
            if path not in path_at_head:
                r = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", path],
                    cwd=REPO, check=False, capture_output=True,
                )
                path_at_head[path] = r.returncode == 0

    print("=== hits by path (HEAD = currently tracked) ===")
    for path in sorted(by_path.keys()):
        uniq = sorted(set(by_path[path]))
        mark = " [HEAD]" if path_at_head.get(path) else ""
        print(f"\n  {path}{mark}  ({len(uniq)} unique leaks)")
        for h in uniq[:5]:
            print(f"    {h}")
        if len(uniq) > 5:
            print(f"    ... +{len(uniq) - 5} more")

    if commit_hits:
        print("\n=== commit message hits (top 10) ===")
        for sha, hits in list(commit_hits.items())[:10]:
            uniq = sorted({h.decode('utf-8', 'replace') for h in hits})
            print(f"  {sha[:10]}")
            for h in uniq[:3]:
                print(f"    {h}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
