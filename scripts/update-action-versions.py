#!/usr/bin/env python3
"""Update GitHub Action versions and pre-commit hook versions from centralized pins.

Reads action-versions.yml and applies SHA-pinned versions to workflow files
and/or pre-commit configs in a target repository.

Usage:
    update-action-versions.py [--actions] [--pre-commit] <repo-path>
    update-action-versions.py --actions --pre-commit /path/to/repo
    update-action-versions.py /path/to/repo  # defaults to --actions
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

VERSIONS_FILE = Path(__file__).parent.parent / "versions" / "action-versions.yml"

# Matches: `uses: owner/repo@ref` or `uses: owner/repo/path@ref`
# Captures: (indent + prefix), (owner/repo), (optional /path), (ref), (optional comment)
USES_RE = re.compile(
    r"^(\s*(?:-\s+)?uses:\s*)"  # group 1: indentation + "uses: "
    r"([\w.-]+/[\w.-]+)"  # group 2: owner/repo
    r"(/[\w./-]*)?"  # group 3: optional sub-path (e.g. /init, /actions/foo)
    r"@"
    r"(\S+)"  # group 4: current ref (tag, sha, branch)
    r"(\s*#.*)?"  # group 5: optional trailing comment
    r"$",
    re.MULTILINE,
)

# Matches: `rev: <value>` in pre-commit config
REV_RE = re.compile(r"^(\s*rev:\s*)(\S+)(\s*#.*)?$", re.MULTILINE)


def load_versions() -> dict:
    with open(VERSIONS_FILE) as f:
        return yaml.safe_load(f)


def update_actions(repo_path: Path, versions: dict) -> int:
    """Update GitHub Action SHA pins in workflow files. Returns count of changes."""
    actions = versions.get("actions", {})
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        print(f"  No .github/workflows/ in {repo_path}")
        return 0

    # Also check composite actions in actions/ dir
    action_dirs = []
    actions_root = repo_path / "actions"
    if actions_root.is_dir():
        for action_yml in actions_root.rglob("action.yml"):
            action_dirs.append(action_yml)

    yml_files = sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml")) + action_dirs
    total_changes = 0

    for yml_file in yml_files:
        content = yml_file.read_text()
        file_changes = 0

        def replace_uses(match: re.Match) -> str:
            nonlocal file_changes
            prefix = match.group(1)
            owner_repo = match.group(2)
            sub_path = match.group(3) or ""
            current_ref = match.group(4)

            if owner_repo in actions:
                pin = actions[owner_repo]
                new_ref = f"{pin['sha']}  # {pin['tag']}"
                # Check if already pinned to same SHA
                if current_ref == pin["sha"]:
                    # Already correct, preserve existing line
                    return match.group(0)
                file_changes += 1
                return f"{prefix}{owner_repo}{sub_path}@{new_ref}"

            # Unknown action — leave as-is
            return match.group(0)

        new_content = USES_RE.sub(replace_uses, content)

        if file_changes > 0:
            yml_file.write_text(new_content)
            rel = yml_file.relative_to(repo_path)
            print(f"  {rel}: {file_changes} action(s) updated")
            total_changes += file_changes

    return total_changes


def update_pre_commit(repo_path: Path, versions: dict) -> int:
    """Update pre-commit hook revs. Returns count of changes."""
    pre_commit_hooks = versions.get("pre_commit", {})
    config_file = repo_path / ".pre-commit-config.yaml"
    if not config_file.is_file():
        print(f"  No .pre-commit-config.yaml in {repo_path}")
        return 0

    content = config_file.read_text()
    _data = yaml.safe_load(content)
    total_changes = 0

    # Build URL-to-rev mapping
    url_to_rev = {}
    for hook_id, pin in pre_commit_hooks.items():
        # hook_id is like "astral-sh/ruff-pre-commit"
        url = f"https://github.com/{hook_id}"
        url_to_rev[url] = pin["rev"]

    # Update revs in raw text (preserve formatting)
    lines = content.splitlines(keepends=True)
    new_lines = []
    current_repo_url = None

    for line in lines:
        # Track which repo block we're in
        repo_match = re.match(r"\s*-\s*repo:\s*(\S+)", line)
        if repo_match:
            current_repo_url = repo_match.group(1)

        # Update rev if we're in a known repo block
        if current_repo_url and current_repo_url in url_to_rev:
            rev_match = re.match(r"^(\s*rev:\s*)(\S+)(.*)$", line)
            if rev_match:
                old_rev = rev_match.group(2)
                new_rev = url_to_rev[current_repo_url]
                if old_rev != new_rev:
                    line = f"{rev_match.group(1)}{new_rev}{rev_match.group(3)}\n"
                    total_changes += 1

        new_lines.append(line)

    if total_changes > 0:
        config_file.write_text("".join(new_lines))
        print(f"  .pre-commit-config.yaml: {total_changes} rev(s) updated")

    return total_changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", type=Path, help="Path to target repository")
    parser.add_argument(
        "--actions", action="store_true", help="Update GitHub Action versions (default if neither flag given)"
    )
    parser.add_argument(
        "--pre-commit", action="store_true", dest="pre_commit", help="Update pre-commit hook versions"
    )
    args = parser.parse_args()

    # Default to --actions if neither specified
    if not args.actions and not args.pre_commit:
        args.actions = True

    if not args.repo_path.is_dir():
        print(f"Error: {args.repo_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    versions = load_versions()
    total = 0

    print(f"Updating {args.repo_path.name}:")

    if args.actions:
        total += update_actions(args.repo_path, versions)

    if args.pre_commit:
        total += update_pre_commit(args.repo_path, versions)

    if total == 0:
        print("  No changes needed.")
    else:
        print(f"  Total: {total} update(s)")

    return 0 if total >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
