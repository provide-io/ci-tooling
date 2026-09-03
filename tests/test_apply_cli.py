# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the CLI that patches resolved pins into pyproject.toml."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import apply_pins

PINS_JSON = json.dumps(
    [
        {
            "package": "provide-foundation",
            "url": "git+https://github.com/provide-io/provide-foundation@feat/x",
            "layer": "dispatch",
        }
    ]
)

BARE = '[project]\nname = "pyvider"\nversion = "1.0.0"\n'


def test_apply_patches_pyproject_and_leaves_a_receipt(tmp_path: Path) -> None:
    project = tmp_path / "pyproject.toml"
    project.write_text(BARE)
    receipt = tmp_path / ".pins-applied.json"

    code = apply_pins.main(
        ["apply", "--pins-json", PINS_JSON, "--pyproject", str(project), "--receipt", str(receipt)]
    )

    assert code == 0
    overrides = tomllib.loads(project.read_text())["tool"]["uv"]["override-dependencies"]
    assert overrides == ["provide-foundation @ git+https://github.com/provide-io/provide-foundation@feat/x"]
    assert json.loads(receipt.read_text())[0]["package"] == "provide-foundation"


def test_clear_restores_pyproject_and_removes_the_receipt(tmp_path: Path) -> None:
    project = tmp_path / "pyproject.toml"
    project.write_text(BARE)
    receipt = tmp_path / ".pins-applied.json"
    apply_pins.main(
        ["apply", "--pins-json", PINS_JSON, "--pyproject", str(project), "--receipt", str(receipt)]
    )

    code = apply_pins.main(["clear", "--pyproject", str(project), "--receipt", str(receipt)])

    assert code == 0
    assert project.read_text() == BARE
    assert not receipt.exists()


PINS_FILE_TEXT = """\
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
when = { event = ["pull_request"] }
"""


def test_local_apply_reads_the_pins_file_and_ignores_its_conditions(tmp_path: Path) -> None:
    project = tmp_path / "pyproject.toml"
    project.write_text(BARE)
    pins_file = tmp_path / "pins.toml"
    pins_file.write_text(PINS_FILE_TEXT)

    code = apply_pins.main(
        [
            "apply",
            "--pins-file",
            str(pins_file),
            "--repo",
            "provide-io/pyvider",
            "--pyproject",
            str(project),
            "--receipt",
            str(tmp_path / ".pins-applied.json"),
        ]
    )

    assert code == 0
    overrides = tomllib.loads(project.read_text())["tool"]["uv"]["override-dependencies"]
    assert overrides == ["provide-foundation @ git+https://github.com/provide-io/provide-foundation@feat/x"]
