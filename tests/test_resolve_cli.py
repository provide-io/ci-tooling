# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the resolve CLI that fronts the pure core in CI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import resolve_pins


def env(tmp_path: Path, **overrides: str) -> dict[str, str]:
    """GitHub-shaped environment pointing GITHUB_OUTPUT at a temp file."""
    base = {
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_HEAD_REF": "feat/x",
        "GITHUB_BASE_REF": "main",
        "GITHUB_REPOSITORY": "provide-io/pyvider",
        "GITHUB_OUTPUT": str(tmp_path / "out.txt"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
    }
    base.update(overrides)
    return base


def outputs(tmp_path: Path) -> dict[str, str]:
    """Parse the GITHUB_OUTPUT file the CLI wrote."""
    lines = (tmp_path / "out.txt").read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line)


def test_resolve_writes_pins_and_digest_to_github_output(tmp_path: Path) -> None:
    code = resolve_pins.main(["--caller-input", "provide-foundation@feat/x"], env(tmp_path))

    assert code == 0
    written = outputs(tmp_path)
    assert json.loads(written["pins"]) == [
        {
            "package": "provide-foundation",
            "url": "git+https://github.com/provide-io/provide-foundation@feat/x",
            "layer": "caller-input",
        }
    ]
    assert written["count"] == "1"
    assert written["digest"] != "none"


def test_resolve_writes_a_step_summary_naming_the_winning_layer(tmp_path: Path) -> None:
    resolve_pins.main(
        ["--dispatch", "provide-foundation@from-dispatch", "--caller-input", "provide-foundation@ignored"],
        env(tmp_path),
    )

    summary = (tmp_path / "summary.md").read_text()
    assert "provide-foundation" in summary
    assert "dispatch" in summary
    assert "ignored" not in summary


def test_resolve_appends_to_the_step_summary_rather_than_replacing_it(tmp_path: Path) -> None:
    (tmp_path / "summary.md").write_text("## Earlier step\n")

    resolve_pins.main(["--caller-input", "provide-foundation@feat/x"], env(tmp_path))

    assert "## Earlier step" in (tmp_path / "summary.md").read_text()


def test_a_rejected_pin_fails_the_step_instead_of_raising(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pins_file = tmp_path / "pins.toml"
    pins_file.write_text(
        '[[pin]]\npackage = "evil"\ngit = "https://github.com/attacker/evil"\nbranch = "main"\n'
    )

    code = resolve_pins.main(["--pins-file", str(pins_file)], env(tmp_path))

    assert code == 1
    assert "outside the allowed orgs" in capsys.readouterr().err
