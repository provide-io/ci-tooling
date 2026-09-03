# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Pure core for branch pins.

No GitHub knowledge, no network, no argv, no environ. Everything a caller needs is
passed in, so the same functions serve the CI wrapper and a local task runner.
"""

from __future__ import annotations

import fnmatch
import hashlib
import tomllib
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


class PinNotAllowedError(Exception):
    """Raised when a pin points somewhere the allowlist does not permit."""


@dataclass(frozen=True)
class Pin:
    """One resolved override: a package forced to a git ref."""

    package: str
    url: str
    layer: str


@dataclass(frozen=True)
class Context:
    """Flattened facts about where resolution is happening."""

    event: str
    head_ref: str
    base_ref: str | None
    labels: tuple[str, ...]
    repo: str
    default_branch: str
    inputs: Mapping[str, str]


@dataclass(frozen=True)
class Layers:
    """Raw, unparsed input from each pin source."""

    dispatch: str | None = None
    labels: tuple[str, ...] = ()
    variable: str | None = None
    file_text: str | None = None
    caller_input: str | None = None
    auto_siblings: tuple[str, ...] = field(default_factory=tuple)


def _parse_short_form(text: str, layer: str, ctx: Context) -> list[Pin]:
    """Expand `pkg@ref` entries into pins under the repository's own org."""
    org = ctx.repo.split("/")[0]
    pins = []
    for entry in text.replace(",", "\n").split("\n"):
        item = entry.strip()
        if not item:
            continue
        package, _, ref = item.partition("@")
        pins.append(
            Pin(
                package=package.strip(),
                url=f"git+https://github.com/{org}/{package.strip()}@{ref.strip()}",
                layer=layer,
            )
        )
    return pins


LABEL_PREFIX = "pin:"


def _parse_labels(labels: Sequence[str], ctx: Context) -> list[Pin]:
    """Turn `pin:<pkg>@<ref>` labels into pins, ignoring every other label."""
    wanted = [item[len(LABEL_PREFIX) :] for item in labels if item.startswith(LABEL_PREFIX)]
    return _parse_short_form("\n".join(wanted), "pr-label", ctx)


def _glob_any(value: str | None, patterns: Sequence[str]) -> bool:
    """True when `value` matches at least one glob; a missing value never matches."""
    return value is not None and any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _matches(when: Mapping[str, Any], ctx: Context) -> bool:
    """Every condition present must match; an absent condition is not a constraint."""
    checks = {
        "event": lambda wanted: ctx.event in wanted,
        "branch": lambda wanted: _glob_any(ctx.head_ref, wanted),
        "base": lambda wanted: _glob_any(ctx.base_ref, wanted),
        "label": lambda wanted: bool(set(wanted) & set(ctx.labels)),
        "input": lambda wanted: all(ctx.inputs.get(k) == v for k, v in wanted.items()),
    }
    return all(check(when[key]) for key, check in checks.items() if key in when)


def _parse_pins_file(text: str, ctx: Context, ignore_conditions: bool) -> list[Pin]:
    """Read the long form: explicit git URL plus optional `when` conditions."""
    document: dict[str, Any] = tomllib.loads(text)
    pins = []
    for entry in document.get("pin", []):
        if not ignore_conditions and not _matches(entry.get("when", {}), ctx):
            continue
        pins.append(
            Pin(
                package=entry["package"],
                url=f"git+{entry['git']}@{entry['branch']}",
                layer="pins-file",
            )
        )
    return pins


def _allowlist_target(url: str) -> str:
    """Reduce a pin URL to `host/owner/repo` for matching, or "" if it is not trustworthy.

    Returning "" for anything unusual keeps the matcher honest: userinfo before the
    host and `..` inside the path both let an allowed-looking prefix resolve
    somewhere else entirely.
    """
    without_ref = url.removeprefix("git+").rsplit("@", 1)[0]
    parsed = urllib.parse.urlsplit(without_ref)
    if parsed.scheme != "https" or "@" in parsed.netloc:
        return ""
    segments = [segment for segment in parsed.path.split("/") if segment]
    if any(segment in {".", ".."} for segment in segments):
        return ""
    return "/".join([parsed.netloc, *segments])


def _check_allowed(pins: Sequence[Pin], allowed_orgs: Sequence[str]) -> None:
    """Reject any pin whose host/org is not allowlisted.

    Layers can carry attacker-influenced text on a public repo, so an unexpected
    destination is a hard failure rather than a skipped pin.
    """
    for pin in pins:
        target = _allowlist_target(pin.url)
        if not target or not any(fnmatch.fnmatch(target, pattern) for pattern in allowed_orgs):
            raise PinNotAllowedError(
                f"{pin.package}: {pin.url} is outside the allowed orgs {list(allowed_orgs)}"
            )


def resolve_pins(
    layers: Layers,
    ctx: Context,
    allowed_orgs: Sequence[str],
    *,
    ignore_conditions: bool = False,
) -> list[Pin]:
    """Collapse every layer into the final per-package pin list.

    Layers are applied highest-precedence first and the first mention of a package
    wins, so a lower layer can add packages but never redefine one already pinned.

    `ignore_conditions` is for local use: off a runner there is no event, base ref
    or label to test, and a developer asking to pin means every declared pin.
    """
    ordered: list[list[Pin]] = [
        _parse_short_form(layers.dispatch or "", "dispatch", ctx),
        _parse_labels(layers.labels, ctx),
        _parse_short_form(layers.variable or "", "repo-variable", ctx),
        _parse_pins_file(layers.file_text or "", ctx, ignore_conditions),
        _parse_short_form(layers.caller_input or "", "caller-input", ctx),
        _parse_short_form(
            "\n".join(f"{name}@{ctx.head_ref}" for name in layers.auto_siblings),
            "auto-sibling",
            ctx,
        ),
    ]

    for group in ordered:
        _check_allowed(group, allowed_orgs)

    winners: dict[str, Pin] = {}
    for group in ordered:
        for pin in group:
            winners.setdefault(pin.package, pin)
    return list(winners.values())


def pins_digest(pins: Sequence[Pin]) -> str:
    """Short, order-independent digest of the effective pin set.

    Feeds the uv cache suffix: a pinned run must not read or write the cache entry
    an unpinned run uses. The layer is excluded because it does not change what
    gets installed.
    """
    if not pins:
        return "none"
    material = "\n".join(sorted(f"{pin.package}={pin.url}" for pin in pins))
    return hashlib.sha256(material.encode()).hexdigest()[:12]
