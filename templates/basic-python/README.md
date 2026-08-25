# Basic Python template

A starting point for a Python package released to PyPI through Trusted
Publishing. Mirrors the workflows the provide.io Python repositories actually
run, so anything scaffolded from here starts on the same footing rather than
drifting toward it later.

## Files

| File | Purpose |
| --- | --- |
| `.github/workflows/ci.yml` | Calls the reusable CI pipeline: lint, types, tests, coverage gate, security and secret scanning. |
| `.github/workflows/release.yml` | Build, TestPyPI, verify, PyPI, SBOM, sigstore signature, release assets. |
| `scripts/sbom_from_wheel.sh` | Generates a CycloneDX SBOM describing the built wheel, called by `release.yml`. |

## Setting it up

1. Copy `.github/workflows/` and `scripts/` into the new repository.
2. In `release.yml`, replace every `PACKAGE-NAME` with the PyPI distribution
   name and `IMPORT-CHECK` with a snippet that imports the package and binds
   its version to `v` — for example `import my_package; v = my_package.__version__`.
3. Create two GitHub environments, `testpypi` and `pypi`.
4. Configure a Trusted Publisher on
   [test.pypi.org](https://test.pypi.org/manage/account/publishing/) and
   [pypi.org](https://pypi.org/manage/account/publishing/) for this repository,
   workflow `release.yml`, and the matching environment. No API token is
   stored anywhere.
5. Release by creating a GitHub Release. A `workflow_dispatch` is a dry run.

## Why the release workflow is shaped the way it is

**The SBOM has its own job.** Generating it means installing the wheel's whole
dependency closure plus `cyclonedx-bom` from PyPI and executing them. That job
runs with `contents: read` and no OIDC, so none of that code runs next to the
sigstore signing identity or a writable repository token. `sign-and-upload`
does no checkout and installs nothing — it runs pinned actions and `gh`, and
nothing else.

**Every publishing job is gated on the release event.** `skip-existing: true`
is not an access control; it only protects a version that already exists. The
`if: github.event_name == 'release'` guards are what make a dispatch from a
branch a genuine dry run.

**Actions are pinned to commit SHAs.** A tag can be moved; a SHA cannot. The
trailing comment records the version each SHA corresponded to so Dependabot can
still read and bump them.

**`cyclonedx-bom` is pinned inside the script**, for the same reason: it is
third-party code fetched from PyPI and executed during a release.

**The SBOM declares its own subject and checks itself.** `cyclonedx-py
environment` describes an interpreter, not a project, so without `--pyproject`
the document has no root component and the package it is about sits among its
dependencies as one entry of many. The script supplies one, fills in the
version and purl from the wheel filename (`dynamic = ["version"]` leaves
cyclonedx-py nothing to read), and then verifies two things before the file is
accepted: the root component matches the wheel, and every non-extra
`Requires-Dist` from the wheel's metadata is present. The second check is the
one that catches an SBOM describing the wrong environment -- the mistake that
put 77 useless SBOMs into this ecosystem's releases. Set `SBOM_MC_TYPE` to
`application` for a CLI-first distribution; it defaults to `library`.
