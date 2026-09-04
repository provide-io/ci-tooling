# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the check that blocks merging while a pin is active."""

from __future__ import annotations

import json

import pytest
import require_no_pins

PINS = json.dumps(
    [
        {
            "package": "python-hcl2",
            "url": "git+https://github.com/livingstaccato/python-hcl2@int/pyvider-hcl-9",
            "layer": "pr-label",
        }
    ]
)


def test_no_pins_passes() -> None:
    assert require_no_pins.main(["--pins-json", "[]"]) == 0


def test_an_active_pin_blocks_the_merge(capsys: pytest.CaptureFixture[str]) -> None:
    code = require_no_pins.main(["--pins-json", PINS])

    assert code == 1
    err = capsys.readouterr().err
    assert "python-hcl2" in err
    assert "pr-label" in err


def test_the_message_names_every_active_pin(capsys: pytest.CaptureFixture[str]) -> None:
    two = json.dumps(
        [
            {"package": "a", "url": "git+https://github.com/o/a@x", "layer": "pr-label"},
            {"package": "b", "url": "git+https://github.com/o/b@y", "layer": "pins-file"},
        ]
    )

    require_no_pins.main(["--pins-json", two])

    err = capsys.readouterr().err
    assert "a" in err and "b" in err


def test_reporting_without_enforcing_passes_but_still_says_so(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = require_no_pins.main(["--pins-json", PINS, "--enforce", "false"])

    assert code == 0
    out = capsys.readouterr()
    assert "python-hcl2" in out.out + out.err


def test_enforcing_is_the_default() -> None:
    assert require_no_pins.main(["--pins-json", PINS]) == 1
