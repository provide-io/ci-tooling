# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Tests for the pure pin-resolution core."""

from __future__ import annotations

import pytest
from pins_core import (
    DEFAULT_ALLOWED_ORGS,
    Context,
    Layers,
    Pin,
    PinNotAllowedError,
    pins_digest,
    resolve_pins,
)

ALLOWED = ("github.com/provide-io/*",)


def ctx(**overrides: object) -> Context:
    """Build a Context with sensible defaults for tests."""
    base: dict[str, object] = {
        "event": "push",
        "head_ref": "main",
        "base_ref": None,
        "labels": (),
        "repo": "provide-io/pyvider",
        "default_branch": "main",
        "inputs": {},
    }
    base.update(overrides)
    return Context(**base)  # type: ignore[arg-type]


def test_short_form_expands_to_a_git_url_in_the_repos_own_org() -> None:
    pins = resolve_pins(
        Layers(caller_input="provide-foundation@feat/x"),
        ctx(),
        allowed_orgs=ALLOWED,
    )

    assert pins == [
        Pin(
            package="provide-foundation",
            url="git+https://github.com/provide-io/provide-foundation@feat/x",
            layer="caller-input",
        )
    ]


def test_only_labels_with_the_pin_prefix_become_pins() -> None:
    pins = resolve_pins(
        Layers(labels=("bug", "pin:provide-foundation@feat/x", "needs-review")),
        ctx(),
        allowed_orgs=ALLOWED,
    )

    assert pins == [
        Pin(
            package="provide-foundation",
            url="git+https://github.com/provide-io/provide-foundation@feat/x",
            layer="pr-label",
        )
    ]


def test_a_higher_layer_wins_the_package_while_a_lower_layer_still_adds_its_own() -> None:
    pins = resolve_pins(
        Layers(
            dispatch="provide-foundation@from-dispatch",
            labels=("pin:provide-foundation@from-label", "pin:provide-testkit@from-label"),
        ),
        ctx(),
        allowed_orgs=ALLOWED,
    )

    by_package = {pin.package: pin for pin in pins}
    assert by_package["provide-foundation"].layer == "dispatch"
    assert by_package["provide-foundation"].url.endswith("@from-dispatch")
    assert by_package["provide-testkit"].layer == "pr-label"


PINS_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
"""


def test_the_pins_file_supplies_an_explicit_git_url() -> None:
    pins = resolve_pins(Layers(file_text=PINS_FILE), ctx(), allowed_orgs=ALLOWED)

    assert pins == [
        Pin(
            package="provide-foundation",
            url="git+https://github.com/provide-io/provide-foundation@feat/x",
            layer="pins-file",
        )
    ]


PR_ONLY_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
when = { event = ["pull_request"] }
"""


def test_a_pin_gated_on_pull_request_is_skipped_on_a_push() -> None:
    pins = resolve_pins(Layers(file_text=PR_ONLY_FILE), ctx(event="push"), allowed_orgs=ALLOWED)

    assert pins == []


RELEASE_BASE_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
when = { base = ["release/*"] }
"""


def test_a_base_glob_is_matched_against_the_pull_request_target() -> None:
    pins = resolve_pins(
        Layers(file_text=RELEASE_BASE_FILE),
        ctx(event="pull_request", base_ref="main"),
        allowed_orgs=ALLOWED,
    )

    assert pins == []


LABEL_GATED_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
when = { label = ["integration"] }
"""


def test_a_label_gated_pin_stays_off_until_the_label_is_present() -> None:
    without = resolve_pins(Layers(file_text=LABEL_GATED_FILE), ctx(), allowed_orgs=ALLOWED)
    with_label = resolve_pins(
        Layers(file_text=LABEL_GATED_FILE),
        ctx(labels=("integration",)),
        allowed_orgs=ALLOWED,
    )

    assert without == []
    assert [pin.package for pin in with_label] == ["provide-foundation"]


INPUT_GATED_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
when = { input = { suite-mode = "integration" } }
"""


def test_an_input_gated_pin_requires_the_caller_to_supply_that_value() -> None:
    wrong = resolve_pins(
        Layers(file_text=INPUT_GATED_FILE),
        ctx(inputs={"suite-mode": "unit"}),
        allowed_orgs=ALLOWED,
    )
    right = resolve_pins(
        Layers(file_text=INPUT_GATED_FILE),
        ctx(inputs={"suite-mode": "integration"}),
        allowed_orgs=ALLOWED,
    )

    assert wrong == []
    assert [pin.package for pin in right] == ["provide-foundation"]


BRANCH_GATED_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/provide-foundation"
branch = "feat/x"
when = { branch = ["feat/*"] }
"""


def test_a_branch_glob_is_matched_against_the_head_ref() -> None:
    off = resolve_pins(Layers(file_text=BRANCH_GATED_FILE), ctx(head_ref="chore/y"), allowed_orgs=ALLOWED)
    on = resolve_pins(Layers(file_text=BRANCH_GATED_FILE), ctx(head_ref="feat/x"), allowed_orgs=ALLOWED)

    assert off == []
    assert [pin.package for pin in on] == ["provide-foundation"]


HOSTILE_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/attacker/provide-foundation"
branch = "main"
"""


def test_a_git_url_outside_the_allowlist_is_rejected() -> None:
    with pytest.raises(PinNotAllowedError, match="attacker"):
        resolve_pins(Layers(file_text=HOSTILE_FILE), ctx(), allowed_orgs=ALLOWED)


TRAVERSAL_FILE = """
[[pin]]
package = "provide-foundation"
git = "https://github.com/provide-io/../attacker/evil"
branch = "main"
"""


def test_a_path_traversal_cannot_smuggle_a_url_past_the_allowlist() -> None:
    with pytest.raises(PinNotAllowedError):
        resolve_pins(Layers(file_text=TRAVERSAL_FILE), ctx(), allowed_orgs=ALLOWED)


def test_auto_siblings_pin_the_current_branch_at_the_lowest_precedence() -> None:
    pins = resolve_pins(
        Layers(auto_siblings=("provide-foundation",), caller_input="provide-foundation@explicit"),
        ctx(head_ref="feat/x"),
        allowed_orgs=ALLOWED,
    )

    assert [pin.layer for pin in pins] == ["caller-input"]
    assert pins[0].url.endswith("@explicit")


def test_auto_siblings_are_used_when_no_other_layer_names_the_package() -> None:
    pins = resolve_pins(
        Layers(auto_siblings=("provide-foundation",)),
        ctx(head_ref="feat/x"),
        allowed_orgs=ALLOWED,
    )

    assert pins == [
        Pin(
            package="provide-foundation",
            url="git+https://github.com/provide-io/provide-foundation@feat/x",
            layer="auto-sibling",
        )
    ]


def test_the_digest_ignores_pin_order_but_changes_with_the_ref() -> None:
    a = Pin("provide-foundation", "git+https://github.com/provide-io/provide-foundation@x", "dispatch")
    b = Pin("provide-testkit", "git+https://github.com/provide-io/provide-testkit@y", "pins-file")
    moved = Pin("provide-foundation", "git+https://github.com/provide-io/provide-foundation@z", "dispatch")

    assert pins_digest([a, b]) == pins_digest([b, a])
    assert pins_digest([a, b]) != pins_digest([moved, b])
    assert pins_digest([]) == "none"


def test_ignoring_conditions_applies_every_declared_pin() -> None:
    pins = resolve_pins(
        Layers(file_text=PR_ONLY_FILE),
        ctx(event="local"),
        allowed_orgs=ALLOWED,
        ignore_conditions=True,
    )

    assert [pin.package for pin in pins] == ["provide-foundation"]


def test_short_form_can_name_another_owner_for_a_fork() -> None:
    pins = resolve_pins(
        Layers(caller_input="livingstaccato/python-hcl2@main"),
        ctx(),
        allowed_orgs=("github.com/livingstaccato/*",),
    )

    assert pins == [
        Pin(
            package="python-hcl2",
            url="git+https://github.com/livingstaccato/python-hcl2@main",
            layer="caller-input",
        )
    ]


def test_the_default_allowlist_covers_the_suite_and_the_forks() -> None:
    pins = resolve_pins(
        Layers(caller_input="provide-foundation@x,livingstaccato/python-hcl2@y"),
        ctx(),
        allowed_orgs=DEFAULT_ALLOWED_ORGS,
    )

    assert [pin.package for pin in pins] == ["provide-foundation", "python-hcl2"]


def test_short_form_takes_an_explicit_distribution_name() -> None:
    pins = resolve_pins(
        Layers(caller_input="fire=google/python-fire@main"),
        ctx(),
        allowed_orgs=("github.com/google/*",),
    )

    assert pins == [
        Pin(
            package="fire",
            url="git+https://github.com/google/python-fire@main",
            layer="caller-input",
        )
    ]
