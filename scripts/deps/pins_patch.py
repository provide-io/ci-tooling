# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Patch resolved pins into a pyproject.toml, and take them back out again.

Pure text in, text out — no filesystem, no GitHub. uv only honours
`[tool.uv] override-dependencies` from pyproject.toml (`UV_OVERRIDE` and `uv.toml`
are both ignored for project resolution), so mutating this file is the only way to
force a package onto a git ref.
"""

from __future__ import annotations

from collections.abc import Sequence

import tomlkit
from pins_core import Pin


def _requirement(pin: Pin) -> str:
    """PEP 508 direct-reference form uv expects in override-dependencies."""
    return f"{pin.package} @ {pin.url}"


MARKER = "ci-tooling-pins"


def apply_pins(pyproject_text: str, pins: Sequence[Pin]) -> str:
    """Return `pyproject_text` with `pins` merged into override-dependencies.

    A `[tool.ci-tooling-pins]` marker records what was there before, so `clear_pins`
    can put the file back exactly. uv ignores unknown `[tool.*]` tables.
    """
    document = tomlkit.parse(clear_pins(pyproject_text))
    tool = document.setdefault("tool", tomlkit.table(is_super_table=True))
    created_uv = "uv" not in tool
    uv = tool.setdefault("uv", tomlkit.table())
    existing = [str(item) for item in uv.get("override-dependencies", [])]
    pinned_packages = {pin.package for pin in pins}
    kept = [item for item in existing if item.partition("@")[0].strip() not in pinned_packages]

    marker = tomlkit.table()
    marker["created-tool-uv"] = created_uv
    marker["had-overrides"] = "override-dependencies" in uv
    marker["original"] = existing
    tool[MARKER] = marker

    uv["override-dependencies"] = kept + [_requirement(pin) for pin in pins]
    return tomlkit.dumps(document)


def clear_pins(pyproject_text: str) -> str:
    """Return `pyproject_text` with any applied pins removed."""
    document = tomlkit.parse(pyproject_text)
    tool = document.get("tool")
    if tool is None or MARKER not in tool:
        return pyproject_text

    marker = tool.pop(MARKER)
    uv = tool["uv"]
    if marker["created-tool-uv"]:
        del tool["uv"]
    elif marker["had-overrides"]:
        uv["override-dependencies"] = [str(item) for item in marker["original"]]
    else:
        del uv["override-dependencies"]

    if not tool:
        del document["tool"]

    # Removing a table can leave a trailing blank line behind, which would make a
    # clear/apply round-trip dirty the file for no reason.
    return tomlkit.dumps(document).rstrip("\n") + "\n"
