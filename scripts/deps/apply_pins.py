#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["tomlkit>=0.13"]
# ///
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Patch resolved pins into pyproject.toml, or take them back out.

Run with `uv run` so tomlkit is fetched into an ephemeral environment — the project
being patched must not gain a build-time dependency on it. tomlkit rather than a
hand-rolled edit because a second `[tool.uv]` table is a TOML duplicate-key error
and projects may already declare `override-dependencies`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pins_patch
from pins_core import Context, Layers, Pin, resolve_pins

DEFAULT_RECEIPT = ".ci/.pins-applied.json"
DEFAULT_ALLOWED_ORGS = ("github.com/provide-io/*",)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("verb", choices=("apply", "clear"))
    parser.add_argument("--pins-json", default="[]")
    parser.add_argument(
        "--pins-file",
        default=None,
        help="Resolve pins from this file instead of --pins-json, ignoring when-conditions",
    )
    parser.add_argument("--repo", default="", help="owner/name, used to expand short-form pins")
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--receipt", default=DEFAULT_RECEIPT)
    return parser.parse_args(list(argv))


def _local_entries(args: argparse.Namespace) -> list[dict[str, str]]:
    """Resolve the pins file the way a developer means it: every pin, no conditions.

    Off a runner there is no event, base ref or label to test against, so applying
    the conditions would silently do nothing.
    """
    ctx = Context(
        event="local",
        head_ref="",
        base_ref=None,
        labels=(),
        repo=args.repo,
        default_branch="main",
        inputs={},
    )
    layers = Layers(file_text=Path(args.pins_file).read_text())
    pins = resolve_pins(layers, ctx, DEFAULT_ALLOWED_ORGS, ignore_conditions=True)
    return [{"package": p.package, "url": p.url, "layer": p.layer} for p in pins]


def _apply(args: argparse.Namespace) -> int:
    """Write the patched pyproject and record what was applied."""
    entries = _local_entries(args) if args.pins_file else json.loads(args.pins_json)
    pins = [Pin(package=e["package"], url=e["url"], layer=e["layer"]) for e in entries]
    project = Path(args.pyproject)
    project.write_text(pins_patch.apply_pins(project.read_text(), pins), encoding="utf-8")

    receipt = Path(args.receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"applied {len(pins)} pin(s) to {project}")
    return 0


def _clear(args: argparse.Namespace) -> int:
    """Restore the pre-pin pyproject and drop the receipt."""
    project = Path(args.pyproject)
    project.write_text(pins_patch.clear_pins(project.read_text()), encoding="utf-8")
    Path(args.receipt).unlink(missing_ok=True)
    print(f"cleared pins from {project}")
    print("run `uv lock` next: clearing the pins does not remove them from uv.lock")
    return 0


def main(argv: Sequence[str]) -> int:
    """Dispatch to the requested verb."""
    args = _parse_args(argv)
    return _apply(args) if args.verb == "apply" else _clear(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
