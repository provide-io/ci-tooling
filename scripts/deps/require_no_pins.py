#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Fail while any pin is active, so a pull request cannot merge on one.

A pin exists to let a branch be *tested* against unreleased code, not to make it
mergeable. Merging while pinned puts the default branch on a dependency that is
not published: the pin does not travel with the merge, so main would resolve from
the registry and get whatever the pin was compensating for.

This runs as its own job so the distinction stays visible. The tests still go
green against the pinned dependency -- that is the point of pinning -- while this
one check stays red until the pin is gone. Make it a required check in branch
protection and the pull request cannot merge until the dependency ships.

`--enforce false` reports the pins and exits 0 rather than skipping the job. A
required status check that never reports is treated as pending forever, so a job
that disappears when a caller turns the feature off would wedge every pull
request in that repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins-json", default="[]")
    parser.add_argument(
        "--enforce",
        default="true",
        help="false reports the pins and passes, so the check still reports rather than "
        "vanishing — a required check that never arrives blocks a repository forever",
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    """Return 1 while any pin is active, 0 when none are."""
    args = _parse_args(argv)
    pins = json.loads(args.pins_json)
    if not pins:
        print("no active pins — this branch resolves entirely from the registry")
        return 0

    enforcing = args.enforce.strip().lower() not in {"false", "0", "no", ""}
    level = "error" if enforcing else "warning"
    stream = sys.stderr if enforcing else sys.stdout

    verdict = "this branch is not mergeable yet" if enforcing else "not enforced here"
    print(f"::{level}::{len(pins)} active pin(s); {verdict}.", file=stream)
    for pin in pins:
        print(f"::{level}::  {pin['package']} -> {pin['url']}  (from {pin['layer']})", file=stream)
    print(
        f"::{level}::A pin is not carried by the merge. Land the dependency upstream, "
        "release it, then remove the pin.",
        file=stream,
    )
    return 1 if enforcing else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
