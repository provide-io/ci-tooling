# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the guard that keeps pins off the default branch and out of releases."""

from __future__ import annotations

from pathlib import Path

import check_no_pins
import pytest

PINNED = """\
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
"""


def test_missing_pins_file_is_clean(tmp_path: Path) -> None:
    assert check_no_pins.main(["--pins-file", str(tmp_path / "absent.toml")]) == 0


def test_a_declared_pin_fails_the_guard_and_names_the_package(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pins_file = tmp_path / "pins.toml"
    pins_file.write_text(PINNED)

    code = check_no_pins.main(["--pins-file", str(pins_file)])

    assert code == 1
    assert "provide-foundation" in capsys.readouterr().err


def test_a_pins_file_with_no_entries_is_clean(tmp_path: Path) -> None:
    pins_file = tmp_path / "pins.toml"
    pins_file.write_text("# nothing pinned right now\n")

    assert check_no_pins.main(["--pins-file", str(pins_file)]) == 0
