# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the CLI that lists sibling candidates from a project's dependencies."""

from __future__ import annotations

from pathlib import Path

import list_siblings
import pytest

PYPROJECT = """\
[project]
name = "pyvider"
dependencies = ["provide-foundation>=0.4.0", "attrs>=25.4.0"]
"""


def test_it_prints_one_candidate_per_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "pyproject.toml"
    project.write_text(PYPROJECT)

    code = list_siblings.main(["--pyproject", str(project)])

    assert code == 0
    assert capsys.readouterr().out.split() == ["attrs", "provide-foundation"]


def test_a_missing_pyproject_is_not_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = list_siblings.main(["--pyproject", str(tmp_path / "absent.toml")])

    assert code == 0
    assert capsys.readouterr().out.strip() == ""
