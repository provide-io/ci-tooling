# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Consumers pin this repository by tag or commit SHA, so a release changes
nothing for a repository until that repository moves its `uses:` pin. Note that
callers pin in two places: the `uses:` line and the `ref:` of the ci-tooling
checkout used by the TestPyPI verification step.

## [Unreleased]

## [0.4.3] - 2026-08-25

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
