# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Consumers pin this repository by tag or commit SHA, so a release changes
nothing for a repository until that repository moves its `uses:` pin. Note that
callers pin in two places: the `uses:` line and the `ref:` of the ci-tooling
checkout used by the TestPyPI verification step.

## [Unreleased]

## [0.7.0] - 2026-09-03

Branch pins, corrected by use. Everything here came out of pinning a real
repository at a real fork rather than reasoning about it: the short form could
not reach another org, the allowlist rejected the org the forks live in, and a
pin naming the wrong distribution failed silently.

### Added

- **Pins are verified against the lockfile after the sync.** uv accepts an
  override for a package nothing depends on and silently does nothing with it —
  `uv lock` exits 0 and the dependency stays on the registry. So a pin naming a
  distribution that does not exist in the graph produced a green run against
  unpinned code, with the step summary reporting the pin as applied. Every job
  now reads `uv.lock` after installing and fails if a pin is not in it. Catches
  three cases at once: a typo, a package that is not really a dependency, and a
  repository whose name differs from the distribution it ships.

- **`<dist>=<owner>/<repo>@<ref>` in the short form**, for when those differ —
  `google/python-fire` ships `fire`. Without an `=` the distribution name is
  still inferred from the repository name.

### Changed

- **The branch-pins guide leads with the PR label and demotes `.ci/pins.toml`.**
  The file was described as the recommended default, which was wrong for the
  common case: it is a commit you have to remember to delete — the merge guard,
  the release block and the pre-commit hook all exist to compensate for it — and
  re-pinning costs a commit each time, when finding the right ref usually takes
  two or three tries. The guide now says to use a label unless the branch is
  long-lived, the pin needs to be reproducible locally, a reviewer should see it
  in the diff, or it needs `when` conditions. It also spells out that `CI_PINS`
  is repository-wide, so setting it for one branch leaks the pin to `main`.

### Added

- **The short form can name another owner: `<owner>/<package>@<ref>`.** It only
  ever expanded under the current repository's org, so the four layers that need
  no commit — dispatch input, PR label, `CI_PINS` variable, workflow input —
  could not reach a fork living somewhere else. That is the case branch pins
  mostly exist for, and only `.ci/pins.toml` could express it. A bare
  `<package>@<ref>` still assumes the repository's own org.

### Changed

- **The default allowlist covers `github.com/livingstaccato/*` as well as
  `github.com/provide-io/*`.** Forks of third-party packages live there, and the
  old default rejected every one of them. The value now lives in one place,
  `pins_core.DEFAULT_ALLOWED_ORGS`, rather than being repeated across two CLIs
  and four YAML files.

## [0.6.1] - 2026-09-03

Closes a hole in 0.6.0, found by running branch pins against a real repository
rather than a fixture.

### Fixed

- **The pin guards now also catch a lockfile that outlived its pins.** Clearing
  the pins restores `pyproject.toml` but does not re-lock, so uv keeps the
  overrides under `[manifest] overrides` until the next resolve — long enough to
  commit them by accident, and past the point where the receipt file the
  pre-commit hook watches still exists. `check_no_pins.py` reads the lockfile as
  well, and `apply_pins.py clear` now says to run `uv lock`. Found by running the
  feature against `pyvider-rpcplugin` rather than a fixture.

## [0.6.0] - 2026-09-03

One feature: branch pins. A minor rather than a patch because it adds seven
`python-ci` inputs, two actions, and a `pin-guard` job to both the CI and the
release workflow.

Inert unless a caller asks for it -- no pins file, variable, label or input
means nothing is patched and nothing is installed differently. The one change
every caller sees is a uv `cache-suffix`, which shifts cache keys to
`pins-none` and costs a single cold cache fill.

### Added

- **Branch pins: resolve a dependency from a git ref instead of the registry.**
  A pull request can now build against unreleased work in a sibling repository.
  Six layers feed one resolution, ordered so that manual-outside-git beats
  in-git and narrower scope beats wider: `workflow_dispatch` input, PR label
  (`pin:<pkg>@<ref>`), `CI_PINS` repository variable, `.ci/pins.toml`, the
  `package-pins` workflow input, then opt-in sibling-branch matching. Four of
  the six need no commit. Only `.ci/pins.toml` carries `when` conditions
  (`event`, `branch`, `base`, `label`, `input`). Off unless a caller asks for
  it; see `docs/branch-pins.md`.

  uv honours overrides only from `[tool.uv] override-dependencies` in
  `pyproject.toml` — `UV_OVERRIDE` is ignored by `uv sync`/`uv lock`, and the
  same key in a `uv.toml` is accepted and silently ignored — so the file is
  rewritten on the runner and restored from a `[tool.ci-tooling-pins]` marker.
  Overrides do not reach a built distribution: a wheel built with a pin active
  still carries the `Requires-Dist` from `[project] dependencies`.

  Every pin URL is checked against `pin-allowed-orgs` (default
  `github.com/provide-io/*`) as `host/owner/repo`; non-HTTPS URLs, userinfo
  before the host, and `..` in the path are rejected. PR bodies are
  deliberately not a layer — on a public repository that is attacker-controlled
  text reaching dependency resolution.

  The resolved set is hashed into uv's `cache-suffix`, so a pinned run cannot
  poison the cache entry an unpinned run reads.

- **`pin-guard` jobs in `python-ci` and `python-release`.** A pin that outlives
  its branch would silently keep a repository on someone's feature work, so a
  push to the default branch and any release both fail while `.ci/pins.toml`
  declares anything. A pre-commit hook covers the same mistake locally.

- **`deps.pin` / `deps.unpin` wrknv tasks.** Local front door over the same
  scripts CI runs, so a pinned environment is reproducible off a runner. Local
  mode applies every pin in the file and ignores `when` conditions, since there
  is no event, base ref or label to test against.

## [0.5.0] - 2026-09-03

A feature release, and the first cut of the moving `v0` tag since 2026-08-20.
`v0` pointed at `194e51a`, which predates `v0.4.3`, so callers pinned to the
tag never received 0.4.3 either: everything below reaches them at once.

### Added

- **`python-ci` matrix testing covers Python 3.14.** The list was hardcoded as
  `["3.11", "3.12", "3.13"]` in each of the six platform jobs, and
  `matrix-testing` is a boolean, so a caller whose classifiers claimed 3.14 had
  no way to test it. Only affects callers setting `matrix-testing: true`.

### Fixed

- **A commit-SHA pin now covers `scripts/`, not just the workflow file.**
  `python-ci` checked its own scripts out at a hardcoded `ref: v0` in all eight
  platform jobs, so a caller pinning a SHA got immutable orchestration and
  whatever the moving tag pointed at that day. It now uses
  `${{ github.job_workflow_sha }}`, the commit the reusable workflow is itself
  running from, which resolves to whatever the caller pinned. Callers on `@v0`
  are unaffected. This matters because a reusable workflow runs with the
  calling repository's token, which is the reason a caller pins a SHA at all.
- `scripts/`: bound `urlopen`'s `read()` to a typed name, which mypy could not
  otherwise follow.

### Changed

- The `basic-python` template now pins `@v0` for both CI and release, rather
  than `@v0.4.2`; it also carries the release repair path, the SBOM
  root-component fix, and the rest of what the repositories actually run. Two
  unused Jinja templates are gone.
- The release workflow no longer hands a writable token to the jobs that run
  PyPI code.
- `sigstore` pinned at v3.5.0; `astral-sh/setup-uv` bumped 9.0.0 to 10.0.1;
  dependabot no longer offers `gitleaks-action` v3.
- `test-actions` builds its fixtures from scripts rather than inline workflow
  YAML.

### Documentation

- Every example and scaffold pinned `@v0.0.1`, a tag that carries no
  `python-ci.yml` at all -- it predates the file -- so anyone following
  quick-start wrote a `uses:` that cannot resolve. All 43 references across
  `docs/` and `AGENTS.md` now say `@v0`.
- The version-pinning section described a commit SHA as an acceptable
  alternative to a tag. That was not true while `ref: v0` was hardcoded, and is
  true again now; the section says what each pin style actually covers.

## [0.4.3] - 2026-08-25

Versioned as a patch, but it is a minor release: it adds four `python-ci`
inputs. The number was chosen against the release workflow's diff alone, before
the other seventeen commits in the range were read. Left as published rather
than retagged, since consumers pin to it. The next feature release is 0.5.0.

### Added

- **`python-ci` gained four inputs.** `use-wrknv` runs checks through `we run <task>` so CI and local development execute the same commands. `run-tests` lets a caller take the pipeline without the test job. `no-sources` passes `--no-sources` to `uv sync`, for suite repositories that point siblings at `../<repo>` editable path dependencies: CI checks out one repository, those paths do not exist on the runner, and the install step went red before a single check ran. `include-windows-arm` splits Windows arm64 out from `include-windows`, which had gated both Windows jobs together — and anything depending on grpcio or cryptography cannot pass on windows-11-arm, because grpcio 1.83.0 publishes win32 and win_amd64 wheels only (grpc/grpc#39064) and cryptography 50.0.0 publishes win_amd64 only. The choice was no Windows coverage or a permanently red job, and every repository picked the former. All four default to their previous behaviour.

### Changed

- **The release workflow's jobs no longer inherit a writable token.** Only `github-release` needs `contents: write`, and it declares that itself. The other jobs declared nothing, and a called workflow's jobs inherit whatever the caller granted at the `uses:` site — which every caller sets to `contents: write`, because `github-release` needs it. So `pre-release-tests` and `build`, the jobs that resolve and install a project's entire dependency tree from PyPI and then execute it, ran with a token that could write to the repository. A workflow-level `permissions: contents: read` makes read the default; a job added later starts read-only unless it asks otherwise.

- **`templates/basic-python` matches what the repositories actually run.** It had drifted to the point of being unusable: its `uses:` paths pointed at `provide-io/ci-tooling/workflows/...`, a directory that does not exist, so anything scaffolded from it would not have run at all. Past that it carried floating `@v4` action tags and a long-lived `PYPI_TOKEN` instead of Trusted Publishing, and represented none of the SBOM, signing or job separation the real workflows carry. It now ships pinned action SHAs, Trusted Publishing, an isolated SBOM job, publishing gated on the release event, `scripts/sbom_from_wheel.sh`, and a README explaining the placeholders and the reasoning behind the job split.

### Fixed

- **Secret scanning was scanning nothing.** gitleaks-action v3.0.0 requires a `GITLEAKS_LICENSE` secret for organization-owned repositories, which no consumer repository has. Every secret-scan job was soft-failing under `continue-on-error` and reporting nothing. Pinned back to v2.3.9, which predates the license requirement.

- **The test-timeout scaling knob was dead code.** provide-foundation ships `apply_timeout_factor()` to scale timeouts via `PROVIDE_TEST_TIMEOUT_FACTOR`, for polling-based tests racing tight timing windows against CPU contention from other pytest-xdist workers. Nothing in CI ever set the variable. Set here, so every repository on this workflow gets it; a no-op for repositories that do not reference it.

### Removed

- `templates/standard-release.yml` and `templates/standard-ci.yml`. Nothing referenced them, no repository used their model — scavenging artifacts from a previous CI run — and both granted `contents: write` plus `id-token: write` across the whole workflow, the CI one for trusted publishing it never performed.

- `templates/ci-python.yml.tmpl` and `templates/wrknv-python.toml.tmpl`. Jinja templates with no renderer anywhere in this repository or in wrknv, both behind whatever they were meant to seed.

### Internal

- `test-actions.yml`'s two fixture setups moved out of 57 lines of inline `run:` heredoc into `ci/` scripts, per this repository's own policy, where they can be read, shellchecked and run locally. No behaviour change.

- Dependency bumps: `actions/checkout` 6.0.2 → 7.0.1, `actions/setup-python` 6.2.0 → 7.0.0, `astral-sh/setup-uv` 8.0.0 → 9.0.0, `codecov/codecov-action` 6.0.0 → 7.0.0.

## [0.4.2] - 2026-04-23

### Changed

- TestPyPI publish and verification dropped from the reusable release workflow; publishing lives in caller workflows. PyPI Trusted Publishing matches on the OIDC `job_workflow_ref`, which points at the workflow that runs the publish action — so publishing from here would require every project's trusted publisher to name `provide-io/ci-tooling`, defeating per-repository isolation. Callers consume the `release-artifacts` artifact and run their own publish jobs.

## [0.4.1] - 2026-04-23

### Added

- TestPyPI verification and release-event gating in the reusable release workflow.

## [0.4.0] - 2026-04-21

### Added

- The 0.4 line of reusable workflows (`python-ci.yml`, `python-release.yml`, `python-security.yml`) and the composite actions they build on.

---

Releases before 0.4.0 (0.0.0 through 0.2.3, September 2025) predate this file
and are not reconstructed here; see the git history.

[Unreleased]: https://github.com/provide-io/ci-tooling/compare/v0.4.3...HEAD
[0.4.3]: https://github.com/provide-io/ci-tooling/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/provide-io/ci-tooling/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/provide-io/ci-tooling/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/provide-io/ci-tooling/releases/tag/v0.4.0
