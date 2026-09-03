# Branch Pins

Force a package to resolve from a git ref instead of the registry, so a pull
request in one repository can build against unreleased work in a sibling — or in
a fork.

Most of the time, reach for a label:

```bash
gh pr edit 12 --add-label 'pin:provide-foundation@feat/new-telemetry'
gh pr edit 12 --add-label 'pin:livingstaccato/python-hcl2@fix/heredoc-line-end'
```

Nothing to commit, nothing to remember to delete. The pin is scoped to the pull
request and disappears when it closes. Re-pinning is editing a label, which
matters more than it sounds: finding the right ref usually takes two or three
tries.

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

### Which one to use

**A PR label, by default.** It costs no commit, cannot outlive the pull request,
and cannot leak to another branch. Setting one needs write access, so it is a
safe layer even on a public repository.

**A `workflow_dispatch` input** when you want to re-run without touching the PR
at all. It needs one-time scaffolding in the calling workflow — a
`workflow_dispatch` trigger with a `package-pins` input, passed through to
`python-ci.yml`.

**`.ci/pins.toml`** when one of these actually applies:

- the branch is long-lived and several people check it out, and they should get
  the same dependency without being told
- you want the pin reproducible locally, via `we run deps.pin`
- a reviewer should see the dependency in the diff
- the pin needs `when` conditions, which no other layer carries

It is a commit you have to remember to delete, which is why the merge guard, the
release block and the pre-commit hook all exist. Worth it when the list above
applies; noise on a solo iteration loop.

**`CI_PINS`, carefully.** The variable is repository-*wide* and persistent: set
it for one branch and every other branch picks it up too, `main` included. Use it
only when the pin genuinely applies to the whole repository for a while, and
unset it deliberately.

**`auto-pin-siblings`** is opt-in and stays that way. It makes the build depend
on state outside the commit — a branch appearing or being deleted elsewhere
changes what this repository installs — and two unrelated repositories can share
a branch name by coincidence.

## Short form

Layers 1, 2, 3 and 5 take `<package>@<ref>` or `<owner>/<package>@<ref>`, comma-
or newline-separated.

Without an owner the repository's own organization is assumed, which covers
sibling repositories:

```
provide-foundation@feat/x
```

With an owner it reaches a fork living somewhere else — the case these pins
mostly exist for:

```
livingstaccato/python-hcl2@fix/heredoc-line-end
```

When the distribution name differs from the repository name, say so with
`<dist>=<owner>/<repo>@<ref>`:

```
fire=google/python-fire@main
```

This matters more than it looks. The name uv keys an override on is the
*distribution* name — what `Requires-Dist` says — and it is not always the
repository name, nor the import name: `provide-foundation` imports as `provide`,
`python-hcl2` imports as `hcl2`. Get it wrong and uv accepts the override for a
package nothing depends on and silently does nothing, so the run goes green
against an unpinned dependency.

CI catches that: after `uv sync`, every pin is checked against the lockfile and
the job fails if one did not take effect. The same check catches a typo and a
package that simply is not a dependency.

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
is pinned to it. See *Which one to use* above for why this stays opt-in.

## Security

Every pin URL is checked against `pin-allowed-orgs`, matched as
`host/owner/repo`. The default is
`github.com/provide-io/*,github.com/livingstaccato/*` — the suite, plus where
forks of third-party packages live. A URL that does not match fails the job
rather than being skipped. Non-HTTPS URLs, userinfo before
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

Local application reads `.ci/pins.toml` — a label lives on the pull request and
is not visible to your laptop. This is the one thing the file buys that no other
layer does.

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
