#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Resolve branch pins from every layer and publish them as step outputs.

Stdlib only, and deliberately so: this runs before uv is installed, because the
digest it emits becomes the uv cache suffix. A pinned run must never share a cache
entry with an unpinned one.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from pins_core import (
    DEFAULT_ALLOWED_ORGS,
    Context,
    Layers,
    Pin,
    PinNotAllowedError,
    pins_digest,
    resolve_pins,
)


def _split(value: str) -> tuple[str, ...]:
    """Split a comma- or newline-separated list, dropping blanks."""
    return tuple(item.strip() for item in value.replace(",", "\n").split("\n") if item.strip())


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dispatch", default="")
    parser.add_argument("--variable", default="")
    parser.add_argument("--caller-input", default="")
    parser.add_argument("--pins-file", default=".ci/pins.toml")
    parser.add_argument("--auto-siblings", default="")
    parser.add_argument("--allowed-orgs", default=",".join(DEFAULT_ALLOWED_ORGS))
    parser.add_argument("--labels-json", default="[]")
    parser.add_argument("--inputs-json", default="{}")
    return parser.parse_args(list(argv))


def _context(args: argparse.Namespace, env: Mapping[str, str]) -> Context:
    """Flatten the GitHub environment into the core's plain-data Context."""
    return Context(
        event=env.get("GITHUB_EVENT_NAME", "push"),
        head_ref=env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME", ""),
        base_ref=env.get("GITHUB_BASE_REF") or None,
        labels=tuple(json.loads(args.labels_json)),
        repo=env.get("GITHUB_REPOSITORY", ""),
        default_branch=env.get("GITHUB_DEFAULT_BRANCH", "main"),
        inputs=json.loads(args.inputs_json),
    )


def _layers(args: argparse.Namespace, ctx: Context) -> Layers:
    pins_file = Path(args.pins_file)
    return Layers(
        dispatch=args.dispatch,
        labels=ctx.labels,
        variable=args.variable,
        file_text=pins_file.read_text() if pins_file.is_file() else None,
        caller_input=args.caller_input,
        auto_siblings=_split(args.auto_siblings),
    )


def _write_summary(env: Mapping[str, str], pins: Sequence[Pin]) -> None:
    """Record the effective pins in the job summary so a reviewer sees them."""
    summary = env.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    lines = ["## 📌 Branch pins", ""]
    if pins:
        lines += ["| Package | Ref | Layer |", "|---|---|---|"]
        lines += [f"| {pin.package} | `{pin.url}` | {pin.layer} |" for pin in pins]
    else:
        lines.append("No pins active — dependencies resolved normally.")
    with Path(summary).open("a", encoding="utf-8") as handle:
        handle.write("\n".join([*lines, ""]))


def main(argv: Sequence[str], env: Mapping[str, str]) -> int:
    """Resolve every layer and write `pins`, `digest` and `count` step outputs."""
    args = _parse_args(argv)
    ctx = _context(args, env)
    try:
        pins = resolve_pins(_layers(args, ctx), ctx, _split(args.allowed_orgs))
    except PinNotAllowedError as error:
        print(f"::error::rejected pin: {error}", file=sys.stderr)
        return 1

    payload = [{"package": p.package, "url": p.url, "layer": p.layer} for p in pins]
    _write_summary(env, pins)
    output = Path(env["GITHUB_OUTPUT"])
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"pins={json.dumps(payload)}\n")
        handle.write(f"digest={pins_digest(pins)}\n")
        handle.write(f"count={len(pins)}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:], dict(__import__("os").environ)))
