#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Confirm that every resolved pin actually took effect.

uv accepts an override for a package nothing depends on and silently does
nothing with it: `uv lock` exits 0 and the dependency stays on the registry. So a
pin naming the wrong distribution -- a typo, a package that is not really a
dependency, or a repository whose name differs from what it ships, as
`google/python-fire` ships `fire` -- produces a green run against unpinned code.

This reads the lockfile after the sync and insists the pin is visible there.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
import urllib.parse
from collections.abc import Sequence
from pathlib import Path


def _normalize(name: str) -> str:
    """PEP 503 name normalization, so `Foo_Bar` and `foo-bar` compare equal."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _pin_target(url: str) -> tuple[str, str]:
    """Split a pin URL into its repository URL and requested ref."""
    without_scheme = url.removeprefix("git+")
    repo, _, ref = without_scheme.rpartition("@")
    return repo, ref


def _locked_git(entry: dict) -> tuple[str, str] | None:
    """Repository URL and ref a locked package came from, or None if not from git."""
    git = entry.get("source", {}).get("git")
    if not git:
        return None
    base, _, query = git.partition("?")
    rev = urllib.parse.parse_qs(query.partition("#")[0]).get("rev", [""])[0]
    return base, urllib.parse.unquote(rev)


def _failures(pins: Sequence[dict], packages: dict[str, dict]) -> list[str]:
    """One message per pin that did not survive into the lockfile."""
    problems = []
    for pin in pins:
        entry = packages.get(_normalize(pin["package"]))
        if entry is None:
            problems.append(
                f"{pin['package']}: not a dependency of this project, so the override did nothing. "
                "Check the distribution name -- it is not always the repository name."
            )
            continue

        locked = _locked_git(entry)
        wanted = _pin_target(pin["url"])
        if locked is None:
            problems.append(
                f"{pin['package']}: still resolved from {entry.get('source', {})}, not from {pin['url']}."
            )
        elif locked != wanted:
            problems.append(f"{pin['package']}: locked to {locked}, expected {wanted}.")
    return problems


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins-json", default="[]")
    parser.add_argument("--lock-file", default="uv.lock")
    return parser.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    """Return 1 when any pin failed to take effect, 0 when they all did."""
    args = _parse_args(argv)
    pins = json.loads(args.pins_json)
    if not pins:
        return 0

    lock_file = Path(args.lock_file)
    if not lock_file.is_file():
        print(f"::error::{lock_file} is missing, so no pin can be verified", file=sys.stderr)
        return 1

    locked = tomllib.loads(lock_file.read_text()).get("package", [])
    packages = {_normalize(entry["name"]): entry for entry in locked}

    problems = _failures(pins, packages)
    for problem in problems:
        print(f"::error::pin did not take effect -- {problem}", file=sys.stderr)
    if problems:
        return 1

    print(f"verified {len(pins)} pin(s) against {lock_file}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
