# Branch Pins

Force a package to resolve from a git ref instead of the registry, so a pull
request in one repository can build against unreleased work in a sibling.

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0
    with:
      package-pins: 'provide-foundation@feat/new-telemetry'
```

## How it works

uv honours dependency overrides only from `[tool.uv] override-dependencies` in
`pyproject.toml`. `UV_OVERRIDE` is ignored by `uv sync` and `uv lock`, and
`override-dependencies` in a `uv.toml` is accepted as a key but has no effect on
project resolution. So CI rewrites `pyproject.toml` on the runner, before the
first `uv sync`, and never commits the result.

The patch is recorded under a `[tool.ci-tooling-pins]` marker table, which uv
ignores, so `apply_pins.py clear` can restore the file exactly.

Overrides do **not** reach a built distribution. A wheel built with a pin active
still carries the `Requires-Dist` from `[project] dependencies`.

## The layers

Six sources feed one resolution. **Manual-outside-git beats in-git; narrower
scope beats wider.** The highest layer wins per package, so a lower layer can add
packages but never redefine one already pinned.

| # | Layer | Commit? | Scope | How to set it |
|---|---|---|---|---|
| 1 | `workflow_dispatch` input | no | this run | `gh workflow run ci.yml -f package-pins='provide-foundation@feat/x'` |
| 2 | PR label | no | this PR | `gh pr edit 12 --add-label 'pin:provide-foundation@feat/x'` |
| 3 | `CI_PINS` repo/org variable | no | this repo | `gh variable set CI_PINS --body 'provide-foundation@feat/x'` |
| 4 | `.ci/pins.toml` | yes | this branch | commit the file on your branch |
| 5 | `package-pins` workflow input | yes | this repo | edit the calling workflow |
| 6 | auto sibling-branch match | no | this branch | `auto-pin-siblings: true` |

Layer 1 needs one-time scaffolding in the calling workflow — a
`workflow_dispatch` trigger with a `package-pins` input, passed through to
`python-ci.yml`. After that, pinning never touches a file again.

`.ci/pins.toml` remains the recommended default: it is the only layer that is
reproducible on a laptop, visible in review, and covered by the merge guard.

## Short form

Layers 1, 2, 3 and 5 take `<package>@<ref>`, comma- or newline-separated. The URL
is expanded under the repository's own organization.

## Long form with conditions

Only `.ci/pins.toml` carries conditions.

```toml
[[pin]]
package = "provide-foundation"
git     = "https://github.com/provide-io/provide-foundation"
branch  = "feat/x"

[pin.when]
event  = ["pull_request"]                 # github.event_name
branch = ["feat/*"]                       # head ref, glob
base   = ["main"]                         # pull request target, glob
label  = ["integration"]                  # gate only
input  = { suite-mode = "integration" }   # matched against pin-inputs-json
```

A pin with no `when` always applies. Every condition present must match.

## Auto sibling-branch matching

```yaml
with:
  auto-pin-siblings: true
  sibling-repos: 'provide-foundation,provide-testkit,pyvider-rpcplugin'
```

Any listed repository that has a branch of the same name as the current head ref
is pinned to it. Off by default, and deliberately so: it makes the build depend
on state outside the commit, and two unrelated repositories can share a branch
name by coincidence.

## Security

Every pin URL is checked against `pin-allowed-orgs` (default
`github.com/provide-io/*`), matched as `host/owner/repo`. A URL that does not
match fails the job rather than being skipped. Non-HTTPS URLs, userinfo before
the host, and `..` in the path are all rejected outright.

Labels and repository variables are safe sources because setting either requires
`triage`/`write` or admin on the repository — a fork contributor has neither.
Pull request **bodies** are deliberately not a layer: on a public repository that
is attacker-controlled text flowing into dependency resolution.

## Lifecycle

A pin that outlives its branch silently keeps a repository on someone's feature
work. Three guards:

- **Merge guard** — `pin-guard` fails a push to the default branch while
  `.ci/pins.toml` declares anything.
- **Release block** — `python-release.yml` will not build while any pin is
  declared.
- **Local guard** — a pre-commit hook refuses to commit `pyproject.toml` or
  `uv.lock` while pins are applied to the working tree, and also refuses a
  `uv.lock` that still carries `[manifest] overrides`. Clearing the pins
  restores `pyproject.toml` but does not re-lock, so run `uv lock` afterwards.

## Locally

```bash
we run deps.pin      # apply .ci/pins.toml to pyproject.toml
we run deps.unpin    # restore it
```

Without wrknv:

```bash
uv run --no-project .ci-tooling/scripts/deps/apply_pins.py apply --pins-file .ci/pins.toml
uv run --no-project .ci-tooling/scripts/deps/apply_pins.py clear
```

Local mode applies every pin in the file and ignores `when` conditions: off a
runner there is no event, base ref or label to test against, so evaluating them
would silently do nothing.

## Caching

The resolved pin set is hashed into a short digest that becomes uv's
`cache-suffix`. Without it, a pinned run would write its dependency cache under
the key an unpinned run reads.
