#!/usr/bin/env python3
"""Run match-on-message remapping for any repo whose summaries.jsonl has stale SHAs.

For each repo, if the current jsonl has entries whose hashes don't resolve,
match via (subject, file-list-overlap) against the current repo and rewrite.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
REPOS = [
    "provide-foundation", "provide-foundry", "provide-telemetry",
    "provide-terminal", "provide-testkit", "provide-workspace",
    "pyvider", "pyvider-components", "pyvider-cty", "pyvider-hcl",
    "pyvider-rpcplugin", "pyvider-schema", "pyvider-telemetry", "wrknv",
]

DATE_WINDOW_DAYS = 7
MIN_JACCARD = 0.25

SHA_RE = re.compile(r'"hash":\s*"([0-9a-f]{40})"')


def run(args, repo, stdin=None):
    return subprocess.run(args, cwd=repo, input=stdin, check=False, capture_output=True).stdout


def all_shas_resolve(repo: Path, shas: list[str]) -> bool:
    if not shas:
        return True
    stdout = run(
        ["git", "cat-file", "--batch-check=%(objecttype)"],
        repo, stdin=("\n".join(shas) + "\n").encode(),
    ).decode("utf-8", "replace")
    return all("commit" in line for line in stdout.splitlines())


def build_commit_index(repo: Path):
    out = run([
        "git", "log", "--all",
        "--pretty=format:__COMMIT__%x09%H%x09%ai%x09%s",
        "--name-only",
    ], repo).decode("utf-8", "replace")

    commits = []
    cur_sha = cur_date = cur_subj = None
    cur_files: set[str] = set()

    def flush():
        if cur_sha:
            commits.append((cur_sha, cur_subj, cur_date, cur_files))

    for line in out.splitlines():
        if line.startswith("__COMMIT__\t"):
            flush()
            _, sha, iso, subj = line.split("\t", 3)
            cur_sha, cur_date, cur_subj, cur_files = sha, iso[:10], subj, set()
        elif line.strip():
            cur_files.add(line)
    flush()

    subj_to_shas: dict[str, list[str]] = defaultdict(list)
    date_to_shas: dict[str, list[str]] = defaultdict(list)
    sha_to_data: dict[str, tuple[str, set[str]]] = {}
    for sha, subj, date_str, files in commits:
        subj_to_shas[subj].append(sha)
        date_to_shas[date_str].append(sha)
        sha_to_data[sha] = (date_str, files)
    return subj_to_shas, date_to_shas, sha_to_data


def entry_date(entry: dict):
    d = entry.get("date")
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d") if d else None
    except ValueError:
        return None


def find_by_subject(entry, subj_to_shas, sha_to_data):
    subjects = entry.get("subjects", [])
    all_hits: set[str] = set()
    hit_counts: dict[str, int] = defaultdict(int)
    for subj in subjects:
        for sha in subj_to_shas.get(subj, []):
            all_hits.add(sha)
            hit_counts[sha] += 1
    if not all_hits:
        return None
    if len(all_hits) == 1:
        return next(iter(all_hits))
    edate = entry_date(entry)
    if edate:
        def delta(s):
            try:
                return abs((datetime.strptime(sha_to_data[s][0], "%Y-%m-%d") - edate).days)
            except ValueError:
                return 999
        in_window = [s for s in all_hits if delta(s) <= DATE_WINDOW_DAYS]
        if in_window:
            return max(in_window, key=lambda s: (hit_counts[s], -delta(s)))
    if max(hit_counts.values()) >= 2:
        return max(hit_counts, key=hit_counts.get)
    return None


def find_by_files(entry, date_to_shas, sha_to_data):
    changes = entry.get("changes", [])
    entry_files = {c.get("file") for c in changes if c.get("file")}
    if not entry_files:
        return None
    edate = entry_date(entry)
    if not edate:
        return None
    candidates = []
    for delta in range(-DATE_WINDOW_DAYS, DATE_WINDOW_DAYS + 1):
        ds = (edate + timedelta(days=delta)).strftime("%Y-%m-%d")
        candidates.extend(date_to_shas.get(ds, []))
    best, best_score = None, MIN_JACCARD
    for sha in candidates:
        cfiles = sha_to_data[sha][1]
        if not cfiles:
            continue
        inter = len(entry_files & cfiles)
        if inter == 0:
            continue
        score = inter / len(entry_files | cfiles)
        if score > best_score:
            best, best_score = sha, score
    return best


def remap(repo: Path, jsonl: Path) -> dict:
    # If all existing SHAs resolve, skip
    current_shas = SHA_RE.findall(jsonl.read_text(encoding="utf-8", errors="replace"))
    if current_shas and all_shas_resolve(repo, current_shas):
        return {"repo": repo.name, "status": "already-clean"}

    # Fresh backup before rewriting
    backup = jsonl.with_suffix(".jsonl.pre-match.bak")
    if not backup.exists():
        import shutil
        shutil.copy2(jsonl, backup)

    subj_to_shas, date_to_shas, sha_to_data = build_commit_index(repo)

    total = via_subject = via_files = missing = 0
    out_lines = []
    with backup.open() as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            entry = json.loads(raw)
            new_sha = find_by_subject(entry, subj_to_shas, sha_to_data)
            if new_sha:
                via_subject += 1
            else:
                new_sha = find_by_files(entry, date_to_shas, sha_to_data)
                if new_sha:
                    via_files += 1
            if new_sha:
                entry["hash"] = new_sha
                out_lines.append(json.dumps(entry, ensure_ascii=False))
            else:
                missing += 1

    jsonl.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return {
        "repo": repo.name, "status": "remapped",
        "total": total, "subject": via_subject, "files": via_files, "missing": missing,
    }


def main():
    for name in REPOS:
        repo = BASE / name
        jsonl = BASE / f"{name}.summaries.jsonl"
        if not (repo / ".git").exists() or not jsonl.exists():
            print(f"{name}: skipped (no repo or no jsonl)")
            continue
        result = remap(repo, jsonl)
        print(result)


if __name__ == "__main__":
    main()
