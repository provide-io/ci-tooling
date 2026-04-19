# Contributing to ci-tooling

Shared GitHub Actions and reusable workflows for the provide.io ecosystem. Contributions should keep actions composable, reusable across repos, and free of project-specific assumptions.

## Prerequisites

- `bash` ≥ 5
- `act` (optional, for local action testing)
- Python 3.11+ (for helper scripts)
- A local checkout of at least one repo that consumes these workflows (e.g. `wrknv`, `provide-foundation`) so you can validate changes end-to-end

## Development Setup

```bash
git clone https://github.com/provide-io/ci-tooling
cd ci-tooling
```

No dependencies to install; actions and scripts are self-contained.

## Standards

- **Action quality**: every `actions/*` composite action has a corresponding test in `.github/workflows/test-actions.yml`. Add a case when you add or modify an action.
- **Workflow parity**: reusable workflows (`templates/*`) must work across Linux/macOS/Windows runners unless explicitly documented as platform-specific.
- **Shell**: `#!/usr/bin/env bash` + `set -euo pipefail` at the top of every script. No `bash`-isms in `sh`-annotated files.
- **Scripts ≤ 3 lines inline**: if a workflow `run:` block exceeds 3 lines, extract it to `scripts/`.
- **SPDX headers** required on every source/config file (`# SPDX-FileCopyrightText: Copyright (c) <year> provide.io llc. All rights reserved.` + `# SPDX-License-Identifier: MIT`).

## Commits

- Conventional prefixes: `feat(action): …`, `fix(workflow): …`, `chore(ci): …`, `docs: …`, `refactor: …`, `test: …`.
- Keep subject ≤ 72 chars.
- Do not mention AI assistance. No `Co-Authored-By:` trailers.
- Canonical author email: `code@tim.life` or `code@provide.io`.

## Pull Requests

1. Run `.github/workflows/test-actions.yml` locally via `act` (or confirm it runs green on the PR branch).
1. For reusable-workflow changes, validate against at least one consumer repo before merge.
1. In the PR description, list which consumer repos you verified against.
