#!/usr/bin/env python3
"""Run scan-paths + scan-release-sensitive checks + trufflehog + CoA/binary
checks against every purged repo. Report cleanly."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
REPOS = [
    "provide-foundation", "provide-foundry", "provide-telemetry",
    "provide-terminal", "provide-testkit", "provide-workspace",
    "pyvider", "pyvider-components", "pyvider-cty", "pyvider-hcl",
    "pyvider-rpcplugin", "pyvider-schema", "pyvider-telemetry", "wrknv",
]

ABS_PATH = re.compile(rb"/(?:Users|home)/[a-zA-Z][a-zA-Z0-9_.-]+/[a-zA-Z0-9_./-]+")
ABS_PATH_SKIP = [b"/Users/Shared", b"/home/runner", b"/home/user", b"/home/vscode"]
BAD_EMAILS = [b"tim@nwea.org", b"code@provide.io", b"code@tim.life"]
BINARY_EXTS = (
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".a", ".o", ".obj",
    ".exe", ".dmg", ".pkg", ".zip", ".tar.gz", ".tgz", ".tar.bz2", ".7z",
    ".rar", ".whl", ".egg", ".flavor", ".pspf", ".sqlite", ".sqlite3", ".db",
    ".pdb", ".ilk", ".bak", ".bak2", ".bak3",
)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=False, capture_output=True)


def check_repo(name: str) -> dict:
    repo = BASE / name
    if not (repo / ".git").exists():
        return {"repo": name, "status": "no-repo"}

    # 1. CoA count
    coa = run(["git", "log", "--all", "--format=%B"], repo).stdout
    coa_count = sum(1 for line in coa.splitlines() if b"co-authored-by:" in line.lower())

    # 2. bad email metadata
    emails_raw = run(["git", "log", "--all", "--format=%ae%n%ce"], repo).stdout
    metadata_emails = set(e.strip() for e in emails_raw.split(b"\n") if e.strip())
    bad_meta = [e for e in metadata_emails if any(be in e for be in BAD_EMAILS)]

    # 3. path leaks in blobs (sample — scan all blobs)
    rev = run(["git", "rev-list", "--objects", "--all"], repo).stdout.decode("utf-8", "replace")
    blob_shas = []
    for line in rev.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            blob_shas.append(parts[0])
    typed = run(
        ["git", "cat-file", "--batch-check=%(objecttype) %(objectname)"],
        repo,
    )
    # feed blobs on stdin via a separate Popen
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch-check=%(objecttype) %(objectname)"],
        cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    stdout, _ = proc.communicate(input=("\n".join(blob_shas) + "\n").encode())
    blobs = [
        row.split()[1]
        for row in stdout.decode("utf-8", "replace").splitlines()
        if row.startswith("blob ")
    ]

    # scan each blob for abs paths and bad emails
    path_leaks = bad_email_content = 0
    for sha in blobs:
        data = run(["git", "cat-file", "-p", sha], repo).stdout
        for m in ABS_PATH.findall(data):
            if any(s in m for s in ABS_PATH_SKIP):
                continue
            path_leaks += 1
            break
        if any(be in data for be in BAD_EMAILS):
            bad_email_content += 1

    # 4. binary extensions still in history
    all_paths = set()
    for line in rev.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            all_paths.add(parts[1])
    bin_in_hist = [p for p in all_paths if any(p.endswith(ext) for ext in BINARY_EXTS)]

    # 5. preservation refs?
    refs = run(["git", "for-each-ref", "--format=%(refname)"], repo).stdout.decode()
    pres_refs = [
        r for r in refs.splitlines()
        if "fetch-extra" in r or "fetch-source" in r or r.startswith("refs/backup/")
    ]

    return {
        "repo": name,
        "coa": coa_count,
        "bad_email_metadata": bad_meta,
        "path_leak_blobs": path_leaks,
        "bad_email_blobs": bad_email_content,
        "binary_paths_in_history": len(bin_in_hist),
        "preservation_refs": len(pres_refs),
    }


def main() -> int:
    print(f"{'repo':<22} {'CoA':>4} {'path-leaks':>11} {'bad-email':>10} {'binaries':>9} {'pres-refs':>10}")
    print("-" * 70)
    for name in REPOS:
        r = check_repo(name)
        if r.get("status") == "no-repo":
            print(f"{name:<22} (no repo)")
            continue
        flags = " ".join(
            f"!{k}" for k in ("coa", "path_leak_blobs", "bad_email_blobs",
                              "binary_paths_in_history", "preservation_refs")
            if isinstance(r.get(k), int) and r[k] > 0
        )
        if r["bad_email_metadata"]:
            flags += f" !bad-metadata={r['bad_email_metadata']}"
        print(
            f"{name:<22} {r['coa']:>4} {r['path_leak_blobs']:>11} "
            f"{r['bad_email_blobs']:>10} {r['binary_paths_in_history']:>9} "
            f"{r['preservation_refs']:>10}  {flags}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
