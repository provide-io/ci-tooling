# Git history cleanup playbook

Distilled from the wrknv cleanup pass (72 MB → 2.2 MB, 97% reduction).

## Phase 1 — Inventory (read-only)

```bash
# all paths ever in history
git rev-list --objects --all | awk 'NF>1 {print $2}' | sort -u > /tmp/all-paths.txt
wc -l /tmp/all-paths.txt

# top-level inventory vs. current HEAD
awk -F/ '{print $1}' /tmp/all-paths.txt | sort -u
git ls-files | awk -F/ '{print $1}' | sort -u

# largest historical blobs
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' \
  | awk '$1=="blob" && $2 > 100000 {print $2, $3}' | sort -rn | head -30

# all refs (watch for fetch-extra/fetch-source preservation refs keeping cruft alive)
git for-each-ref --format='%(refname)'
```

## Phase 2 — Categorize what to purge

Scan `/tmp/all-paths.txt` for:

1. **Secrets/keys:** `*.pem *.key *.p12 *.pfx id_rsa* .env .netrc .pypirc .aws/ credentials*`
1. **Binaries/archives:** `*.exe *.dll *.so *.dylib *.pyc *.whl *.tar.gz *.dmg *.pkg`
1. **Committed venvs:** `bin/ lib/python*/ .venv/ pyvenv.cfg site-packages/`
1. **Build outputs:** `build/ dist/ *.egg-info/ site/ htmlcov/ cover/`
1. **Caches:** `__pycache__/ .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage`
1. **Generated outputs:** whatever your tool generates (e.g. wrknv: `env.sh env.ps1`)
1. **Editor detritus:** `*.bak *.bak2 *.swp *.orig *.old *~`
1. **Session dumps:** `TODO.md NOTES.md SESSION_STATUS.md *SUMMARY*.md ARCHITECTURE*.md` at repo root
1. **Timestamped logs:** `20250818-*.txt` etc.
1. **Legacy pre-rename trees:** if repo was renamed (`src/oldname/`), whole old tree often lingers
1. **WIP filename variants:** `*_new.py *_v2.py *.copy`
1. **Ad-hoc top-level scripts:** `fix_*.py migrate_*.py validate_*.py original_*.py`
1. **Archive/stale dirs:** `docs/archive/ docs/stale/ archive/ scraps/`
1. **Local config leaks:** `.claude/ .coverage .env.local *.local.json`
1. **Legacy rename remnants:** old project name in config files

Cross-check each candidate: is it currently tracked at HEAD? If yes, don't purge — clean working-tree cruft first instead.

```bash
for p in <candidates>; do
  git ls-files "$p" >/dev/null 2>&1 && echo "TRACKED: $p" || echo "history-only: $p"
done
```

## Phase 2.5 — Scan blob *content* for absolute-path leakage

Path-based purging catches files. Content-based scanning catches *strings inside files* — absolute filesystem paths like `/Users/<name>/code/...`, `file:///Users/...`, `/REDACTED_TMP`. These are not secrets but reveal username, directory structure, and sibling-project names. **This kind of cruft must be left out of history.**

Common sources:

- `pyproject.toml` with `file:///Users/.../sibling-pkg` local-sibling refs
- Session-log txt files capturing shell output
- Test fixtures / docstrings that hardcoded a dev-machine path
- `.egg-info/` directories auto-generated with absolute build paths

Use [`scan-paths.py`](./scan-paths.py) to enumerate every blob + commit message with abs-path hits. Classify results:

- **Class A — whole path is cruft.** Add the path itself to your `paths-from-file` purge list.
- **Class B — path is legitimate at HEAD, only old revisions leak.** Scrub via `--replace-text`.

For Class B, write `/tmp/replacements.txt`:

```
regex:/Users/[a-zA-Z][a-zA-Z0-9_.-]+/[A-Za-z0-9_./-]+==>/REDACTED_ABS_PATH
regex:/home/[a-zA-Z][a-zA-Z0-9_.-]+/[A-Za-z0-9_./-]+==>/REDACTED_ABS_PATH
regex:/private/var/folders/[A-Za-z0-9_./-]+==>/REDACTED_TMP
```

**Regex must handle `.` in usernames.** `/REDACTED_ABS_PATH` is not the same as `/REDACTED_ABS_PATH`. The pattern above accepts both (`[a-zA-Z0-9_.-]+` covers dotted usernames). A narrower `/Users/tim/` won't catch prior-machine paths where the shell user was `tim`.

Then combine with path removal in one filter-repo pass:

```
git filter-repo --invert-paths \
    --paths-from-file /tmp/purge-paths.txt \
    --replace-text /tmp/replacements.txt \
    --force
```

Whitelist-before-scan: define a `SKIP` list of generic placeholders that are *not* real leaks (`/home/user`, `/home/runner`, `/home/vscode`, `/Users/Shared`) so your scanner doesn't false-positive on them.

**Regex gotcha:** Python `re.findall()` returns group matches when the pattern has a capturing group. Use **non-capturing** groups `(?:...)` in scanner regexes, otherwise your SKIP filter operates on the sub-match and lets everything through.

## Phase 2.6 — Release-sensitive content audit

Beyond filesystem paths, a public release should be free of:

- **Personal emails** other than the project's canonical public addresses
- **Prior-employer domains** (e.g. `nwea.org`, `hmhco.com`) — signals affiliations you don't want to publicize
- **Full-name variants** (e.g. `tim`, `timothy.perkins`) when you prefer a shorter handle publicly
- **Private IPs** (`10.x.x.x`, `192.168.x.x`, `172.16-31.x.x`)
- **Internal SaaS URLs** (company Slack/JIRA/Grafana/Datadog hostnames)
- **Ticket identifiers** from private trackers
- **`file://` URLs pointing to an absolute local path**
- **Embedded URL creds** (`https://user:pass@host/`)
- **Git-metadata leaks** — `git log --all --format='%ae%n%ce' | sort -u` for every author/committer email ever written. Normalize via `git filter-repo --email-callback` if needed.

Run [`scan-release-sensitive.py`](./scan-release-sensitive.py) (customize the `PATTERNS` dict per person/project). Findings that need purging usually fall into:

- **Class A** — blob is cruft, purge the path (`paths-from-file`).
- **Class B** — blob stays, only old revs leak — scrub via `filter-repo --replace-text`.
- **Class C (git metadata)** — emails/names on commits themselves; only `--email-callback` or `--name-callback` fix these. Example:

```bash
git filter-repo --email-callback '
  return b"code@tim.life" if email in (b"old@nwea.org", b"old@hmhco.com") else email
'
```

- **Class D (commit messages)** — email addresses and unwanted metadata lines *inside* commit bodies. `--replace-text` touches blobs only, not messages. Use `--message-callback`:

```bash
git filter-repo \
  --replace-text /tmp/replacements.txt \
  --message-callback '
import re
msg = re.sub(rb"(?im)^\s*Co-Authored-By:.*$\n?", b"", message)
msg = msg.replace(b"old@example.com", b"canonical@example.com")
msg = re.sub(rb"\n{3,}", b"\n\n", msg)
return msg.rstrip() + b"\n"
'
```

Common Class D scrubs:

- Strip `Co-Authored-By:` lines (AI-assistance attribution, teammate emails)
- Rename email addresses inside message bodies to match the canonical author email
- Drop `Signed-off-by:` for public release if your DCO requirements change
- Strip internal ticket refs (`JIRA-1234`) from subjects if relevant

Repeat the scan after each purge until clean.

## Phase 3 — Handle preservation refs first

Check for stealth refs that keep purged content alive:

```bash
git for-each-ref --format='%(refname)' | sed 's|/[^/]*$||' | sort -u
```

If you see `refs/fetch-extra-*`, `refs/fetch-source/*`, `refs/backup/*`, or `refs/stash` — filter-repo won't save you from these. Either delete them up front or filter-repo's gc won't shrink anything:

```bash
# delete in batch
git for-each-ref --format='delete %(refname)' refs/fetch-extra-0/ refs/fetch-extra-1/ \
  | git update-ref --stdin
```

Keep any preservation refs you actually want (or nuke them all if no live remote).

## Phase 4 — Purge

Safety backup first, then filter-repo:

```bash
# safety ref
git update-ref refs/backup/pre-purge HEAD

# write purge list (directories get trailing /; files are literal)
cat > /tmp/purge-paths.txt <<'EOF'
keys/
dist/
lib/
bin/
mutants/
build/
env.sh
env.ps1
EOF

# single filter-repo pass (paths + globs combined)
git filter-repo --invert-paths \
  --paths-from-file /tmp/purge-paths.txt \
  --path-glob '**/*.pyc' \
  --path-glob '**/__pycache__/**' \
  --path-glob '*.bak' --path-glob '**/*.bak' \
  --path-glob '*.bak2' --path-glob '**/*.bak2' \
  --path-glob '*.bak3' --path-glob '**/*.bak3' \
  --force
```

**Glob pitfalls in filter-repo:**

1. **Top-level files:** `**/*.bak` does NOT match `mkdocs.yml.bak` at repo root. The `**/` prefix requires at least one intermediate directory. Always pair `*.bak` (top-level) with `**/*.bak` (nested).
1. **No-extension Unix binaries:** Go/Rust compiled executables have no extension (`flavor-go-builder`, `kv-go-client`, etc.). Extension globs miss them entirely. Enumerate their directories explicitly in `--paths-from-file` (e.g. `src/ingredients/bin/`, `tests/kv/bin/`).
1. **Compressed debug info inside binaries:** committed binaries embed build-machine absolute paths in their debug sections. Even after `--replace-text`, these paths survive because the text is inside binary data. The cure is purging the binary, not scrubbing it.

```bash

# reflog expire + aggressive gc (filter-repo doesn't prune reflog alone)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**filter-repo gotchas:**

- Rewrites *all* commit SHAs. No remote push magic — you'd need to coordinate force-push.
- Only operates on refs it knows about. Non-standard refs (above) survive.
- Drops commits whose entire content was purged.
- Writes `commit-map` at `.git/filter-repo/commit-map` — **keep this** if you have external systems referencing old SHAs.

## Phase 5 — Verify

```bash
# HEAD tree unchanged
git diff --stat refs/backup/pre-purge HEAD   # expect empty

# tests still green (adapt per-project)
pytest -q

# trufflehog (install via brew; scans entire object DB)
trufflehog git file://. --fail --no-update

# size check
du -sh .git
git count-objects -v

# if stuff lingers, something is still preserving old objects
git for-each-ref --format='%(refname)'
```

If trufflehog flags findings, check if they're in dangling/preservation commits vs main. Anything reachable from `refs/heads/main` is a real finding; anything only in `refs/fetch-source/*` or reflog is keepalive cruft — delete the ref and re-gc.

## Phase 6 — Realign external changelogs

If you have `repogerbil`-style `../<repo>.summaries.jsonl` files sitting next to each repo, SHAs inside will now be dead. Two parts:

1. **Hash remap** — `.git/filter-repo/commit-map` has columns `old  new`. Rewrite each `"hash"` field via lookup. ~96% will map cleanly; ~4% get dropped (commits that became empty).
1. **Scrub purged-file references** — remove `changes[]` entries whose `file` is in your purge list. Leave narrative prose unless it's *wholly* about a purged file.

Reference script saved alongside this playbook: [`align-jsonl.py`](./align-jsonl.py). Update the `PURGED_DIRS` / `PURGED_FILES` constants and `JSONL`/`REPO` paths per run. Keep the `.pre-align.bak` the script creates; drop it after verifying all current hashes resolve via `git cat-file -e`.

**Important:** filter-repo's commit-map "old" column is the SHA as it existed at the *start* of the run — so if you do multiple filter-repo passes, the map only covers the most recent pass. Either align after each pass, or save each pass's commit-map and chain them.

**Multi-pass gotcha (learned the hard way):** if you realign after pass-1, then do pass-2 and pass-3 on the same repo, do NOT naively re-run the aligner — the jsonl now holds post-pass-1 SHAs but the commit-map is pass-3's. The aligner will drop almost everything. Options:

1. **Plan every filter-repo pass up front**, then realign once at the end. Best option.
1. **Copy `.git/filter-repo/commit-map` aside before each pass**, then chain them in post-order: `orig → p1 → p2 → p3`.
1. **Accept the drops** — realign uses current commit-map + "keep if SHA still exists in repo" fallback, which keeps unchanged commits but drops the rewritten chain. Fine if the purge is cosmetic (~50%+ loss for heavily-rewritten repos).

The fallback logic in `realign-all-purged.py`:

```python
new = cmap.get(old)
if new is None:
    # commit not in this pass's map — keep if it still exists
    if commit_exists(repo, old):
        new = old
    else:
        drop()
```

## Phase 7 — Drop backup ref

```bash
git update-ref -d refs/backup/pre-purge
```

## Biggest-win patterns (from wrknv)

Most of the size win came from two things:

1. An `auto-commit` that committed an entire `.venv` (`bin/`, `lib/python3.13/site-packages/`) — ~170 MB of historical blob weight despite being dangling.
1. A 67 MB `dist/<name>.flavor` packaged binary.

Accidentally-committed venvs + accidentally-committed build artifacts are typically the big wins. Everything else is rounding error.

## Human items that can't be automated

- **Rotate anything that was a real secret.** If a private key, API token, or credential was in history and anyone ever cloned, it's compromised. Purge doesn't un-ring that bell.
- **Inspect any `keys/` / `*.key` / `*.pem` finds individually** — distinguish test fixtures (leave) from real material (rotate).
- **Decide about lockfiles** (`uv.lock`, `package-lock.json`, `Cargo.lock`). If tracked, each churn is a 300+ KB blob. Either accept that or untrack and shift to regenerating. Not strictly cruft.
