#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Print the sibling candidates implied by a project's own dependencies.

auto-pin-siblings otherwise needs a hand-kept list of repository names in every
caller's workflow -- nine repositories each naming the other eight, drifting
apart independently. A project already declares what it depends on, and a
sibling it does not depend on has no business being pinned, so the dependency
list is both less work and the more correct definition.

Names that are not repositories in the organization simply fail the branch
lookup downstream, so no filtering is needed or attempted here.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from pins_core import sibling_candidates


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", default="pyproject.toml")
    return parser.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    """Print one candidate per line. A project without dependencies prints nothing."""
    args = _parse_args(argv)
    project = Path(args.pyproject)
    if not project.is_file():
        return 0

    for name in sibling_candidates(project.read_text()):
        print(name)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
