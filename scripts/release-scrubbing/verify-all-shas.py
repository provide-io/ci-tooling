#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Verify every hash in every realigned summaries.jsonl resolves in its repo."""

from __future__ import annotations

import re
import subprocess  # nosec
from pathlib import Path

BASE = Path(__file__).parent
REPOS = [
    "provide-foundation",
    "provide-foundry",
    "provide-telemetry",
    "provide-terminal",
    "provide-testkit",
    "provide-workspace",
    "pyvider",
    "pyvider-components",
    "pyvider-cty",
    "pyvider-hcl",
    "pyvider-rpcplugin",
    "pyvider-schema",
    "pyvider-telemetry",
    "wrknv",
]

SHA_RE = re.compile(r'"hash":\s*"([0-9a-f]{40})"')


def main() -> int:
    print(f"{'repo':<24} {'entries':>7} {'resolve':>8} {'missing':>8}")
    print("-" * 50)
    for name in REPOS:
        repo = BASE / name
        jsonl = BASE / f"{name}.summaries.jsonl"
        if not jsonl.exists() or not (repo / ".git").exists():
            print(f"{name:<24} {'n/a':>7}")
            continue
        shas = SHA_RE.findall(jsonl.read_text(encoding="utf-8", errors="replace"))
        if not shas:
            print(f"{name:<24} {'0':>7}")
            continue
        # batch-check all SHAs via cat-file --batch-check
        stdin = "\n".join(shas).encode()
        out = (
            subprocess.run(
                ["git", "cat-file", "--batch-check=%(objecttype)"],
                cwd=repo,
                input=stdin,
                check=False,
                capture_output=True,
            )
            .stdout.decode("utf-8", "replace")
            .splitlines()
        )
        resolved = sum(1 for line in out if "commit" in line)
        missing = len(shas) - resolved
        print(f"{name:<24} {len(shas):>7} {resolved:>8} {missing:>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
