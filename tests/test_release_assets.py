# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the guard that stops a release quietly carrying less than the last."""

from __future__ import annotations

import release_assets

# What pyvider v0.7.0 actually shipped.
V0_7_0 = [
    "pyvider-0.7.0-py3-none-any.whl",
    "pyvider-0.7.0-py3-none-any.whl.sigstore.json",
    "pyvider-0.7.0.tar.gz",
    "pyvider-0.7.0.tar.gz.sigstore.json",
    "sbom-python.cdx.json",
    "sbom-python.cdx.json.sigstore.json",
    "v0.7.0.tar.gz",
    "v0.7.0.tar.gz.sigstore.json",
    "v0.7.0.zip",
    "v0.7.0.zip.sigstore.json",
]

# What the next release would have shipped after `release-signing-artifacts:
# false`: no source archives, no SBOM signature. The regression this exists for.
V0_7_1_REGRESSED = [
    "pyvider-0.7.1-py3-none-any.whl",
    "pyvider-0.7.1-py3-none-any.whl.sigstore.json",
    "pyvider-0.7.1.tar.gz",
    "pyvider-0.7.1.tar.gz.sigstore.json",
    "sbom-python.cdx.json",
]

V0_7_1_COMPLETE = [name.replace("0.7.0", "0.7.1") for name in V0_7_0]


def test_a_version_bump_alone_is_not_a_loss() -> None:
    """The comparison is by shape, so every name changing is not a regression."""
    assert release_assets.missing_shapes(V0_7_0, V0_7_1_COMPLETE, set()) == []


def test_the_signing_regression_is_caught() -> None:
    gone = release_assets.missing_shapes(V0_7_0, V0_7_1_REGRESSED, set())
    # Five of ten, which is what the release would have lost: both source
    # archives, both of their signatures, and the SBOM's signature.
    assert gone == [
        "<v>.tar.gz",
        "<v>.tar.gz.sigstore.json",
        "<v>.zip",
        "<v>.zip.sigstore.json",
        "sbom-python.cdx.json.sigstore.json",
    ]


def test_a_declared_removal_is_allowed() -> None:
    allowed = {
        "<v>.tar.gz",
        "<v>.tar.gz.sigstore.json",
        "<v>.zip",
        "<v>.zip.sigstore.json",
        "sbom-python.cdx.json.sigstore.json",
    }
    assert release_assets.missing_shapes(V0_7_0, V0_7_1_REGRESSED, allowed) == []


def test_extra_assets_are_not_a_failure() -> None:
    """Adding is always fine; this guards shrinkage only."""
    added = [*V0_7_1_COMPLETE, "pyvider-0.7.1.attestation.json"]
    assert release_assets.missing_shapes(V0_7_0, added, set()) == []


def test_shapes_of_the_forms_these_releases_actually_use() -> None:
    cases = {
        "pyvider-0.7.0-py3-none-any.whl": "pyvider-<v>-py3-none-any.whl",
        "v0.7.0.zip.sigstore.json": "<v>.zip.sigstore.json",
        "terraform-provider-pyvider_0.5.0_windows_amd64.zip": "terraform-provider-pyvider_<v>_windows_amd64.zip",
        "tofusoup-0.7.6.tar.gz": "tofusoup-<v>.tar.gz",
        "sbom-python.cdx.json": "sbom-python.cdx.json",
    }
    for name, shape in cases.items():
        assert release_assets.asset_shape(name) == shape, name


def test_prerelease_and_post_versions_normalise() -> None:
    """A prerelease must not read as a different shape than its final."""
    assert release_assets.asset_shape("pkg-1.2.3rc1.tar.gz") == release_assets.asset_shape("pkg-1.2.3.tar.gz")
    assert release_assets.asset_shape("pkg-1.2.3.post2.tar.gz") == release_assets.asset_shape(
        "pkg-1.2.3.tar.gz"
    )


def test_a_platform_matrix_losing_one_target_is_caught() -> None:
    """The provider ships one archive per platform; losing one is a real loss."""
    before = [
        f"terraform-provider-pyvider_0.5.0_{p}.zip" for p in ("linux_amd64", "darwin_arm64", "windows_amd64")
    ]
    after = [f"terraform-provider-pyvider_0.5.1_{p}.zip" for p in ("linux_amd64", "darwin_arm64")]
    assert release_assets.missing_shapes(before, after, set()) == [
        "terraform-provider-pyvider_<v>_windows_amd64.zip"
    ]


def test_a_scoped_allowance_applies_to_its_own_release() -> None:
    honoured, standing = release_assets.applicable_allowances(["sbom-python.cdx.json@v0.7.1"], "v0.7.1")
    assert honoured == {"sbom-python.cdx.json"}
    assert standing == []


def test_a_scoped_allowance_expires_by_itself() -> None:
    """The release after the rename must not still be excused."""
    honoured, _ = release_assets.applicable_allowances(["sbom-python.cdx.json@v0.7.1"], "v0.7.2")
    assert honoured == set()


def test_a_bare_allowance_is_standing_and_reported() -> None:
    honoured, standing = release_assets.applicable_allowances(["<v>.zip"], "v0.7.1")
    assert honoured == {"<v>.zip"}
    assert standing == ["<v>.zip"]


def test_the_sbom_rename_is_excused_once_then_caught() -> None:
    """The exact case this ships for, and the release after it."""
    renamed = [n for n in V0_7_1_COMPLETE if not n.startswith("sbom-")] + [
        "v0.7.1.sbom.cdx.json",
        "v0.7.1.sbom.cdx.json.sigstore.json",
    ]
    scoped = ["sbom-python.cdx.json@v0.7.1", "sbom-python.cdx.json.sigstore.json@v0.7.1"]

    honoured, _ = release_assets.applicable_allowances(scoped, "v0.7.1")
    assert release_assets.missing_shapes(V0_7_0, renamed, honoured) == []

    # v0.7.2 compares against v0.7.1, which already has the new names, so the
    # allowance is not needed -- and would not apply even if left behind.
    later, _ = release_assets.applicable_allowances(scoped, "v0.7.2")
    assert later == set()


def test_a_stale_allowance_is_reported() -> None:
    """An allowance excusing nothing is noise that hides the next real loss."""
    stale = release_assets.unused_allowances(V0_7_0, V0_7_1_COMPLETE, {"<v>.zip"})
    assert stale == ["<v>.zip"]
