# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the sibling-branch lookup that feeds the auto-sibling pin layer.

The script shells out to `gh`, so each test puts a stub on PATH that answers
for a named set of branches. That is what lets the negative case assert "this
lookup finds nothing" without depending on which branches a real repository
happens to carry at the time.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deps" / "find-sibling-branches.sh"

# `gh api repos/<owner>/<repo>/branches/<branch>` exits 0 when the branch is
# there and non-zero when it is not, which is the whole contract used here.
STUB = """\
#!/usr/bin/env bash
for arg in "$@"; do
  case "$arg" in
    repos/*/branches/*)
      for known in $EXISTING_REFS; do
        [ "$arg" = "$known" ] && exit 0
      done
      exit 1
      ;;
  esac
done
exit 1
"""


def _run(tmp_path: Path, *, siblings: str, branch: str, existing: str) -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "gh"
    stub.write_text(STUB)
    stub.chmod(0o755)

    output = tmp_path / "gh_output"
    output.touch()

    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "OWNER": "provide-io",
        "BRANCH": branch,
        "SIBLINGS": siblings,
        "GITHUB_OUTPUT": str(output),
        "EXISTING_REFS": existing,
    }
    subprocess.run(["bash", str(SCRIPT)], env=env, check=True, capture_output=True)
    return output.read_text()


def test_a_sibling_carrying_the_branch_is_found(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        siblings="provide-foundation,provide-testkit",
        branch="main",
        existing="repos/provide-io/provide-foundation/branches/main",
    )

    assert result == "found=provide-foundation\n"


def test_every_matching_sibling_is_found(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        siblings="provide-foundation,provide-testkit",
        branch="main",
        existing=(
            "repos/provide-io/provide-foundation/branches/main repos/provide-io/provide-testkit/branches/main"
        ),
    )

    assert result == "found=provide-foundation,provide-testkit\n"


def test_a_branch_no_sibling_carries_finds_nothing(tmp_path: Path) -> None:
    """The negative case the workflow asserts, with the world held still."""
    result = _run(
        tmp_path,
        siblings="provide-foundation,provide-testkit",
        branch="absent-12345-1",
        existing="repos/provide-io/provide-foundation/branches/main",
    )

    assert result == "found=\n"


def test_the_branch_name_reaches_the_api_unaltered(tmp_path: Path) -> None:
    """A slash in a branch name is part of the ref, not a path to rewrite."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    asked = tmp_path / "asked"
    stub = bin_dir / "gh"
    stub.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$2" >> {asked}\nexit 1\n')
    stub.chmod(0o755)
    output = tmp_path / "gh_output"
    output.touch()

    subprocess.run(
        ["bash", str(SCRIPT)],
        env={
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "OWNER": "provide-io",
            "BRANCH": "feat/x",
            "SIBLINGS": "provide-foundation",
            "GITHUB_OUTPUT": str(output),
        },
        check=True,
        capture_output=True,
    )

    assert asked.read_text() == "repos/provide-io/provide-foundation/branches/feat/x\n"


def test_an_empty_sibling_list_is_not_an_error(tmp_path: Path) -> None:
    """No candidates means no lookup, not a failure: ci-tooling declares none."""
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nname = "ci-tooling"\ndependencies = []\n')

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "gh"
    stub.write_text(STUB)
    stub.chmod(0o755)
    output = tmp_path / "gh_output"
    output.touch()

    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "OWNER": "provide-io",
        "BRANCH": "main",
        "SIBLINGS": "",
        "PINS_PYPROJECT": str(project),
        "GITHUB_OUTPUT": str(output),
        "EXISTING_REFS": "",
    }
    subprocess.run(["bash", str(SCRIPT)], env=env, check=True, capture_output=True)

    assert output.read_text() == "found=\n"


@pytest.mark.parametrize("missing", ["OWNER", "BRANCH"])
def test_a_missing_required_variable_fails_loudly(tmp_path: Path, missing: str) -> None:
    """`${VAR:?}` is what stops a lookup running against an empty name."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "gh"
    stub.write_text(STUB)
    stub.chmod(0o755)
    output = tmp_path / "gh_output"
    output.touch()

    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "OWNER": "provide-io",
        "BRANCH": "main",
        "SIBLINGS": "provide-foundation",
        "GITHUB_OUTPUT": str(output),
        "EXISTING_REFS": "",
    }
    env.pop(missing)

    result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True)

    assert result.returncode != 0
