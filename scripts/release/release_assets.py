# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Refuse a release that carries less than the one before it.

A release can lose an artifact without anything failing. The workflow that
attaches them reports success for what it did attach, so a step that stops
producing a file -- a signing input dropped, a glob that no longer matches, an
action flag flipped -- ships a release that looks complete and is not. It was
caught once by reading an action's source and diffing two releases by hand; the
next one would not be.

Assets are compared as *shapes* rather than names: every version-looking token
is replaced, so `pyvider-0.7.0-py3-none-any.whl` and its 0.7.1 successor are the
same shape and can be compared across releases.

This does not judge whether the set is right, only whether it shrank. A
deliberate removal is declared with --allow-missing.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - the GitHub CLI is the interface to releases

#: Matches a release-looking version anywhere in a filename: 1.2.3, v1.2.3,
#: 1.2.3rc1, 1.2.3.post2, 1.2.3-beta.1.
#:
#: The prerelease markers are enumerated rather than accepting any trailing
#: token. "Any token" swallows the extension -- `pyvider-0.7.0-py3-none-any.whl`
#: collapses to `pyvider-<v>`, and so does the `.tar.gz` beside it, which makes
#: every artifact the same shape and the comparison useless.
_VERSION = re.compile(r"v?\d+\.\d+\.\d+(?:[-.]?(?:a|b|c|rc|alpha|beta|dev|post|pre)[-.]?\d+)?")


def asset_shape(name: str) -> str:
    """The version-independent shape of an asset name.

    `pyvider-0.7.0-py3-none-any.whl` -> `pyvider-<v>-py3-none-any.whl`
    `v0.7.0.zip.sigstore.json`       -> `<v>.zip.sigstore.json`
    """
    return _VERSION.sub("<v>", name)


def shapes(names: list[str]) -> set[str]:
    return {asset_shape(name) for name in names}


def missing_shapes(previous: list[str], current: list[str], allowed: set[str]) -> list[str]:
    """Shapes the previous release had that this one does not, minus allowances."""
    return sorted(shapes(previous) - shapes(current) - allowed)


def _assets(repo: str, tag: str) -> list[str]:
    result = subprocess.run(  # nosec B603 B607
        ["gh", "release", "view", tag, "--repo", repo, "--json", "assets"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [asset["name"] for asset in json.loads(result.stdout)["assets"]]


def _previous_tag(repo: str, tag: str) -> str | None:
    """The release published before this one, or None if this is the first.

    Ordered by the API's own listing rather than by parsing versions: a release
    that was re-cut or back-dated should still compare against what a consumer
    actually saw before it.
    """
    result = subprocess.run(  # nosec B603 B607
        ["gh", "release", "list", "--repo", repo, "--limit", "50", "--json", "tagName,isDraft"],
        capture_output=True,
        text=True,
        check=True,
    )
    tags = [r["tagName"] for r in json.loads(result.stdout) if not r["isDraft"]]
    if tag not in tags:
        return tags[0] if tags else None
    index = tags.index(tag)
    return tags[index + 1] if index + 1 < len(tags) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="the release being checked, e.g. v0.7.1")
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument(
        "--allow-missing",
        action="append",
        default=[],
        metavar="SHAPE",
        help="a shape this release drops on purpose, e.g. '<v>.zip.sigstore.json'",
    )
    args = parser.parse_args(argv)

    previous = _previous_tag(args.repo, args.tag)
    if previous is None:
        print(f"no release before {args.tag}; nothing to compare against")
        return 0

    before = _assets(args.repo, previous)
    after = _assets(args.repo, args.tag)
    gone = missing_shapes(before, after, set(args.allow_missing))

    if not gone:
        print(f"✅ {args.tag} carries every shape {previous} did ({len(after)} assets)")
        return 0

    print(f"::error::{args.tag} is missing {len(gone)} asset shape(s) that {previous} carried:")
    for shape in gone:
        print(f"::error::  {shape}")
    print(f"::error::{previous} had {len(before)} assets, {args.tag} has {len(after)}.")
    print("::error::If a removal is deliberate, declare it with --allow-missing '<shape>'.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

# 📦🔍🔚
