#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Realign ../<repo>.summaries.jsonl after a filter-repo purge.

- Remaps each `hash` via .git/filter-repo/commit-map (original -> new SHA).
- Drops entries whose commit was eliminated (content entirely purged).
- Strips `changes[]` entries whose `file` matches PURGED_DIRS/FILES.

Usage:
  1. Set REPO to the repo directory. JSONL is auto-derived as ../<reponame>.summaries.jsonl.
  2. Populate PURGED_DIRS (trailing slash) and PURGED_FILES (exact paths) to match
     whatever you just ran through `git filter-repo --invert-paths`.
  3. Run: `python3 align-jsonl.py`. A `.pre-align.bak` is written next to the jsonl.

Re-runs after multiple filter-repo passes: the commit-map reflects only the most
recent pass, so restore from the oldest .pre-align.bak before each re-run, or
chain the maps manually.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec
import sys
from pathlib import Path

# -- configure per repo ------------------------------------------------------
REPO = Path("/Volumes/data/pyv/REPONAME")
JSONL = REPO.parent / f"{REPO.name}.summaries.jsonl"
COMMIT_MAP = REPO / ".git" / "filter-repo" / "commit-map"
BACKUP = JSONL.with_suffix(".jsonl.pre-align.bak")

# directories whose contents were purged (always include trailing "/")
PURGED_DIRS: tuple[str, ...] = (
    # "keys/",
    # "dist/",
    # "lib/",
    # "bin/",
    # "mutants/",
    # "site/",
    # "build/",
)

# exact file paths that were purged
PURGED_FILES: frozenset[str] = frozenset(
    [
        # "large_file.bin",
        # "env.sh",
    ]
)

# glob-style rules applied in is_purged() below (edit to taste)
PURGE_PYC_AND_PYCACHE = True
PURGE_BAK_SUFFIXES = (".bak", ".bak2", ".bak3")
# ---------------------------------------------------------------------------

ZERO_SHA = "0" * 40


def load_commit_map(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    with path.open() as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 2 or parts[0] == "old":
                continue
            result[parts[0]] = parts[1]
    return result


def commit_exists(sha: str) -> bool:
    rc = subprocess.run(
        ["git", "cat-file", "-e", sha],
        cwd=REPO,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode
    return rc == 0


def is_purged(path: str) -> bool:
    if path in PURGED_FILES:
        return True
    if any(path.startswith(d) or path == d.rstrip("/") for d in PURGED_DIRS):
        return True
    if PURGE_PYC_AND_PYCACHE and (path.endswith(".pyc") or "__pycache__" in path):
        return True
    base = path.rsplit("/", 1)[-1]
    return bool(PURGE_BAK_SUFFIXES and base.endswith(PURGE_BAK_SUFFIXES))


def transform(entry: dict, cmap: dict[str, str]) -> dict | None:
    old = entry.get("hash")
    if not old:
        return entry
    new = cmap.get(old)
    if not new or new == ZERO_SHA or not commit_exists(new):
        return None
    entry["hash"] = new
    changes = entry.get("changes", [])
    entry["changes"] = [c for c in changes if not is_purged(c.get("file", ""))]
    return entry


def main() -> int:
    if not REPO.is_dir():
        print(f"error: REPO not a directory: {REPO}", file=sys.stderr)
        return 1
    if not JSONL.exists():
        print(f"error: {JSONL} missing", file=sys.stderr)
        return 1
    if not COMMIT_MAP.exists():
        print(f"error: {COMMIT_MAP} missing - run filter-repo first", file=sys.stderr)
        return 1

    cmap = load_commit_map(COMMIT_MAP)
    shutil.copy2(JSONL, BACKUP)

    total = dropped = rewritten = scrubbed = 0
    out_lines: list[str] = []
    with JSONL.open() as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            entry = json.loads(raw)
            before = len(entry.get("changes", []))
            result = transform(entry, cmap)
            if result is None:
                dropped += 1
                continue
            after = len(result.get("changes", []))
            scrubbed += before - after
            rewritten += 1
            out_lines.append(json.dumps(result, ensure_ascii=False))

    JSONL.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"total={total} rewritten={rewritten} dropped={dropped} scrubbed_file_refs={scrubbed}")
    print(f"backup at {BACKUP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
