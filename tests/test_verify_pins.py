# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the check that a pin actually took effect."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import verify_pins

PINS = json.dumps(
    [
        {
            "package": "python-hcl2",
            "url": "git+https://github.com/livingstaccato/python-hcl2@fix/heredoc-line-end",
            "layer": "pr-label",
        }
    ]
)

LOCK_PINNED = """\
version = 1

[[package]]
name = "python-hcl2"
version = "0.1.dev1"
source = { git = "https://github.com/livingstaccato/python-hcl2?rev=fix%2Fheredoc-line-end#abc123" }
"""

LOCK_UNPINNED = """\
version = 1

[[package]]
name = "python-hcl2"
version = "8.1.3"
source = { registry = "https://pypi.org/simple" }
"""

LOCK_ABSENT = """\
version = 1

[[package]]
name = "packaging"
version = "25.0"
source = { registry = "https://pypi.org/simple" }
"""


def run(tmp_path: Path, lock_text: str, pins: str = PINS) -> int:
    lock = tmp_path / "uv.lock"
    lock.write_text(lock_text)
    return verify_pins.main(["--pins-json", pins, "--lock-file", str(lock)])


def test_a_pin_that_took_effect_passes(tmp_path: Path) -> None:
    assert run(tmp_path, LOCK_PINNED) == 0


def test_a_pin_the_lockfile_ignored_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = run(tmp_path, LOCK_UNPINNED)

    assert code == 1
    assert "python-hcl2" in capsys.readouterr().err


def test_a_pin_for_a_package_nothing_depends_on_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run(tmp_path, LOCK_ABSENT)

    assert code == 1
    assert "not a dependency" in capsys.readouterr().err


def test_no_pins_is_trivially_verified(tmp_path: Path) -> None:
    assert run(tmp_path, LOCK_ABSENT, pins="[]") == 0


LOCK_NORMALIZED = """\
version = 1

[[package]]
name = "python-hcl2"
version = "0.1.dev1"
source = { git = "https://github.com/livingstaccato/python-hcl2?rev=fix%2Fheredoc-line-end#abc123" }
"""

MIXED_CASE_PINS = json.dumps(
    [
        {
            "package": "Python_HCL2",
            "url": "git+https://github.com/livingstaccato/python-hcl2@fix/heredoc-line-end",
            "layer": "pr-label",
        }
    ]
)


def test_package_names_compare_after_pep_503_normalization(tmp_path: Path) -> None:
    assert run(tmp_path, LOCK_NORMALIZED, pins=MIXED_CASE_PINS) == 0


def test_a_pin_locked_to_the_wrong_ref_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    lock = LOCK_PINNED.replace("fix%2Fheredoc-line-end", "some-other-branch")

    code = run(tmp_path, lock)

    assert code == 1
    assert "expected" in capsys.readouterr().err
