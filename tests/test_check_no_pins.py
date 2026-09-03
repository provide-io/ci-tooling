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


LOCK_WITH_OVERRIDES = """\
version = 1
revision = 3
requires-python = ">=3.11"

[manifest]
overrides = [{ name = "provide-foundation", git = "https://github.com/provide-io/provide-foundation?rev=main" }]
"""

LOCK_CLEAN = """\
version = 1
revision = 3
requires-python = ">=3.11"
"""


def test_a_lockfile_still_carrying_overrides_fails_the_guard(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text(LOCK_WITH_OVERRIDES)

    code = check_no_pins.main(["--pins-file", str(tmp_path / "absent.toml"), "--lock-file", str(lock)])

    assert code == 1
    assert "provide-foundation" in capsys.readouterr().err


def test_a_lockfile_without_overrides_is_clean(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text(LOCK_CLEAN)

    assert check_no_pins.main(["--pins-file", str(tmp_path / "absent.toml"), "--lock-file", str(lock)]) == 0
