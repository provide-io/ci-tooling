# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for patching pins into pyproject.toml."""

from __future__ import annotations

import tomllib

from pins_core import Pin
from pins_patch import apply_pins, clear_pins

FOUNDATION = Pin(
    package="provide-foundation",
    url="git+https://github.com/provide-io/provide-foundation@feat/x",
    layer="dispatch",
)

BARE = """\
[project]
name = "pyvider"
version = "1.0.0"
dependencies = ["provide-foundation>=1.0"]
"""


def test_apply_adds_the_override_when_the_project_has_no_tool_uv_table() -> None:
    patched = apply_pins(BARE, [FOUNDATION])

    parsed = tomllib.loads(patched)
    assert parsed["tool"]["uv"]["override-dependencies"] == [
        "provide-foundation @ git+https://github.com/provide-io/provide-foundation@feat/x"
    ]


EXISTING = """\
[project]
name = "pyvider"
version = "1.0.0"

[tool.uv]
# keep me
package = false
override-dependencies = ["python-hcl2 @ git+https://github.com/provide-io/python-hcl2@main"]
"""


def test_apply_keeps_other_tool_uv_settings_and_pre_existing_overrides() -> None:
    patched = apply_pins(EXISTING, [FOUNDATION])

    uv = tomllib.loads(patched)["tool"]["uv"]
    assert uv["package"] is False
    assert set(uv["override-dependencies"]) == {
        "python-hcl2 @ git+https://github.com/provide-io/python-hcl2@main",
        "provide-foundation @ git+https://github.com/provide-io/provide-foundation@feat/x",
    }
    assert "# keep me" in patched


def test_clear_restores_pre_existing_overrides_and_settings() -> None:
    restored = clear_pins(apply_pins(EXISTING, [FOUNDATION]))

    uv = tomllib.loads(restored)["tool"]["uv"]
    assert uv["override-dependencies"] == ["python-hcl2 @ git+https://github.com/provide-io/python-hcl2@main"]
    assert uv["package"] is False


def test_clear_removes_the_tool_uv_table_it_had_to_create() -> None:
    restored = clear_pins(apply_pins(BARE, [FOUNDATION]))

    assert "tool" not in tomllib.loads(restored)


def test_clear_is_a_no_op_when_nothing_was_applied() -> None:
    assert clear_pins(EXISTING) == EXISTING
