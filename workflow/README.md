# `workflow/`: AutoSE agent code, prompts and GitHub workflows

This directory is the source of truth for everything that runs in the fork (`vishesh312/tinydb`).
`sync_to_fork.sh` copies it there. The design lives in `../architecture/DESIGN.md`, and the
reasons behind it are in `../architecture/decisions/`.

## Layout and architecture-to-code map

| Path | What it implements | Design reference |
|---|---|---|
| `autose/pipeline.py` | The in-job state machine: S1 → S2 → S3 ⇄ S4, design revisit, rework entry points (S2/S3/S4). `next_stage()` is the routing table as a pure function. Also covers the no-progress detector, the run cost cap, the job deadline and the rework reservation. | DESIGN §2, §2.1, §3; ADR-002, ADR-006, ADR-009, ADR-013 |
| `autose/checks.py` | Every deterministic check. S1 spec structure + judge verdicts. S2 path existence, AST symbol lookup (`Class.method`), AC coverage, `tinydb/**` only. S3 per-agent path allowlist (snapshot diff, including untracked files) plus compileall/import/mypy. S4 AC→collected tests, full suite, `mypy tinydb tests`, fails-on-base in a temporary `git worktree`. S6 review validity rules and routing. | DESIGN §2, §8; ADR-005 (layer 4), ADR-007 |
| `autose/agent.py` | The runner interface and envelope parsing, `ClaudeRunner` (legacy `claude -p --bare …` backend, ADR-011), `FakeRunner` (scripted, zero cost), the token-free agent env, and the one-pass `{{NAME}}` template renderer, which fails on unfilled placeholders and neutralises fence tags in values. | DESIGN §6, §14; ADR-005, ADR-011 |
| `autose/backends.py` | The subscription runners: `CodexRunner` (default; `codex exec` with OS sandbox, network off, strict `--output-schema`, repo `AGENTS.md` ignored) and `AgyRunner` (Antigravity CLI, used only for the reviewer/verifier in E1's cross-vendor arm), both returning the same envelope shape; `NOTIONAL_PRICES` and the notional list-price-equivalent cost of each call. | DESIGN §6, §7; ADR-014 |
| `autose/review.py` | The S6 Reviewer run (one re-ask if invalid), the Verifier pass over `important` findings (ADR-015), reading `.autose/REVIEW.md` from the base commit, and the post-review decision (CI result, stale SHA, invalid → awaiting-human, approve, route, final). | DESIGN §2 S6, §2.1, §9, §10; ADR-008, ADR-013, ADR-015 |
| `autose/github.py` | `gh` wrappers, all with `--repo`. Covers issue + trusted comments (collaborator permission API), the sticky status comment, labels, PR create/update, the trace comment, the COMMENT review, commit status, and the human-commit guard. | DESIGN §5, §6, §10, §10.1; ADR-004, ADR-005, ADR-010 |
| `autose/render.py` | `spec.md`, `design.md`, `test_report.md` (rendered by the orchestrator, never by the Tester), `pr.md`, `review.md`, the status comment, and `## Stop reason` sections. | DESIGN §2.1, §5, §14 |
| `autose/ledger.py` | `state.json` and `ledger.jsonl` (including `cache_write`). | DESIGN §5, §14; ADR-004 |
| `autose/config.py` | Roles (model, effort, tools, allow rules, budget, turns, timeout), the backend per role and its default models (`BACKEND_MODELS`), caps, the review reserve, allowlists, env overrides. | DESIGN §6, §7, §10; ADR-005, ADR-006, ADR-014 |
| `autose/cli.py` | Subcommands: `gate`, `build`, `review --prepare / --no-github`, `post-review`, `rework`, `finalize`, `local` (E2), `review-local` (E1), `canary`. | DESIGN §3; ADR-002, ADR-010 |
| `autose/schemas/*.schema.json` | The JSON contracts for spec, judge, design, dev_notes, test_map, review, verify and builder. | DESIGN §14 |
| `prompts/`, `skills/` | Agent prompts and the A1 skill (written separately; see `prompts/README.md`). | ADR-003, ADR-008 |
| `github-workflows/autose.yml` | gate → build → round1..3 → finalize, plus the manual `canary` job. | DESIGN §3, §6, §11 |
| `github-workflows/autose-round.yml` | Reusable round: rework? → ci → review (isolated) → post. | DESIGN §3, §6; ADR-008 |
| `github-workflows/ci.yml` | Fork CI (pytest + mypy); when it is called, it posts the `autose-ci` commit status. | DESIGN §2 S5 |
| `tests/` | Unit tests plus FakeRunner end-to-end tests (no network, no LLM). | |

### Stage → agent → check

| Stage | Agent / code | Check (decided by the orchestrator) |
|---|---|---|
| S1 | Analyst (+ single-call Judge) | schema, AC structure, judge says every AC is testable, no blocking question (else `needs-info`) |
| S2 | Architect | schema, paths exist or are new, `modify` symbols found by AST, AC coverage, `tinydb/**` only |
| S3 | Developer | only `tinydb/**` touched, non-empty diff, compileall + import + mypy |
| S4 | Tester | only `tests/test_autose_issue_<N>.py` touched, every AC → collected test, ≥1 new test fails on base, full suite + `mypy tinydb tests` |
| S5 | code | push with lease, PR open, CI (`autose-ci`) success |
| S6 | Reviewer (separate job, no token) + Verifier per `important` finding | schema + evidence rules; only `important` findings that survive verification route (approach → S2, code → S3, tests → S4), at most 2 send-backs |

## How a build or rework job is split (security)

Each build and rework job runs three steps, so the Codex login and the GitHub token are never in the same process:

1. **prepare** (has `GH_TOKEN`): writes `issue.json` (title, body, comments from write-access users) and
   `branch.json` (the result of the human-commit check) to `$AUTOSE_HOME/issue-<N>/input/`, and adds a "started" line to the status comment.
2. **agent** (has the `CODEX_AUTH_JSON` secret, written to `$RUNNER_TEMP/codex-home/auth.json` (mode 600) with `CODEX_HOME`
   pointing at it and deleted by an `if: always()` step; **no** GitHub token; the command refuses to run if one is present): runs S1–S4
   offline from those files, then commits only `tinydb/**` and the test file (after `git reset`, so anything an agent staged is dropped).
3. **publish** (has `GH_TOKEN`, no Codex login): runs a final gate (`git diff --name-only --no-renames base HEAD` must stay
   inside the allowlist), sets up push credentials (in this step only), force-pushes with lease, creates or updates the PR,
   and writes the trace comment, labels and status timeline.

`$AUTOSE_HOME` is outside `work/`. With the legacy `claude` backend agents run with `--restricted`, so their file
tools cannot read the artifacts. **With the default `codex` backend this is not enforced:** Codex's `read-only` and
`workspace-write` sandboxes restrict writes and network, not reads, so an agent that went looking could read
`$AUTOSE_HOME` (for example the Tester reading `dev_notes.json` or Developer logs). The prompts do not point
agents there, and the review job never has the build artifacts on disk, so reviewer independence is unaffected;
the Developer/Tester hand-off exclusions of DESIGN §4 rely on the prompt for this backend. The reviewer's probe directory is separate from its artifact directory. Every orchestrator `git` call
runs with hooks and fsmonitor disabled and a scrubbed environment.

### Residual concurrency race

The workflow-level group `autose-<N>` serialises real triggers for the same issue or PR number. A label on issue
#N and a `/autose` comment on its PR #M are different numbers, so two runs for the same canonical issue can
interleave. Job-level groups were removed on purpose, because a pending job in such a group can cancel another
run's pending round. What protects us instead:

- `post-review` discards a review whose reviewed SHA is no longer the PR head (`stale`).
- Pushes use `--force-with-lease` against the head that was just read.
- The human-commit guard refuses to reset a branch that has non-bot commits.

The worst remaining outcome is a wasted round, or one run's stale review being discarded. Wrong code is never
merged, because a human merges.

## Running locally

Requirements: Python ≥ 3.10 with `jsonschema` (plus `pytest` and `pyyaml` for the tests), and a tinydb
checkout with its own venv (pytest, pytest-cov, mypy).

```bash
cd workflow
python -m pip install jsonschema pytest pyyaml

# unit + FakeRunner end-to-end tests (no LLM calls)
AUTOSE_TEST_TINYDB=/path/to/clean/tinydb python -m pytest tests -q

# E2 (Developer/Tester split vs single Builder), from frozen spec/design
python -m autose --home ../results/e2 --python /path/to/tinydb/.venv/bin/python \
  local --issue-file ../experiment/issues/issue-1.md --repo /path/to/fresh/tinydb \
  --stages 3-4 --freeze-dir ../results/frozen/issue-1 --variant split   # or: single

# capture frozen spec/design for E2 (S1-S2 only)
python -m autose --home ../results/frozen-run --python … local --issue-file … --repo … --stages 1-2

# E1 (independent vs friendly reviewer) on a seeded PR dir: issue.md + diff.patch [+ friendly_context/]
python -m autose --home ../results/e1 --python … review-local \
  --pr-dir ../experiment/seeded_prs/<id> --repo /path/to/tinydb --variant independent   # or: friendly

# scripted experiment drivers (from the repo root): E1 all arms, E2 both variants, hidden-test scoring
#   ../experiment/scripts/run_e1.sh, run_e2.sh, score.py (see ../experiment/variants.md)

# zero-cost dry run of any of the above with scripted agents
python -m autose --fake tests/fixtures/pop … local …
```

`local` works on `--repo` in place, using `HEAD` as the base, so give it a fresh checkout.
`review-local` applies the diff in a throwaway `git worktree` and leaves `--repo` untouched.
All artifacts go under `--home` (default `$AUTOSE_HOME` or `./.autose-home`): `issue-<N>/` holds
`spec.*`, `design.*`, `diff.patch`, `dev_notes.json`, `test_map.json`, `test_report.md`, `pr.md`,
`state.json`, `ledger.jsonl`, `summary.json` and `logs/` (the task prompts and raw CLI envelopes for each call).

## Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `AUTOSE_HOME` | artifact directory | `./.autose-home` |
| `AUTOSE_PYTHON` | interpreter of the target project (checks; its directory is put first on the agents' `PATH`) | `python` |
| `AUTOSE_MODEL_<ROLE>`, `AUTOSE_EFFORT_<ROLE>`, `AUTOSE_BUDGET_<ROLE>`, `AUTOSE_MAX_TURNS_<ROLE>`, `AUTOSE_TIMEOUT_<ROLE>` | per-role overrides (`ANALYST`, `JUDGE`, `ARCHITECT`, `DEVELOPER`, `TESTER`, `REVIEWER`, `VERIFIER`, `REVIEWER_FRIENDLY`, `BUILDER`); empty means unset | DESIGN §7 |
| `AUTOSE_RUN_CAP_USD` | run cost cap, in notional list-price-equivalent $ (ADR-014); build and rework always leave one Reviewer cap plus one Verifier cap free (the invalid-review re-ask is not reserved) | `10` |
| `AUTOSE_VERIFY` | `0` skips the ADR-015 verification pass (and returns the Verifier cap to the reserve) | `1` |
| `AUTOSE_PRICE_<MODEL>` | `in,cached,out` USD per 1M tokens for the notional cost of a model (e.g. `AUTOSE_PRICE_GPT_6_1_SOL`) | `NOTIONAL_PRICES` |
| `AUTOSE_JOB_DEADLINE` | epoch seconds when the job is killed; no agent call starts with less than its timeout + `AUTOSE_DEADLINE_SLACK_MIN` (2) left | unset (no deadline) |
| `AUTOSE_SANDBOX=1` | legacy `claude` backend: turn on Claude Code's bash sandbox (no network, key denied to commands); in CI it also installs bubblewrap. The `codex` backend always sandboxes agent commands; the orchestrator's own check subprocesses are not sandboxed by this flag | off |
| `AUTOSE_FAKE` / `--fake DIR` | use `FakeRunner` with `DIR/script.json` | off |
| `AUTOSE_BACKEND`, `AUTOSE_BACKEND_<ROLE>` | agent backend, globally or per role; the workflows set `codex` | `codex` |
| `AUTOSE_CODEX` | path to the `codex` binary | `codex` |
| `AUTOSE_AGY` | path to the `agy` binary (E1 cross-vendor arm) | `agy` |
| `CODEX_HOME` | directory holding Codex's ChatGPT login `auth.json` (in CI: `$RUNNER_TEMP/codex-home`, agent steps only) | `~/.codex` |
| `AUTOSE_CLAUDE` | path to the `claude` binary (legacy Claude backend) | `claude` |
| `AUTOSE_PROMPTS_DIR`, `AUTOSE_SKILL_FILE` | prompt locations | next to the package |
| `AUTOSE_BOT_NAME`, `AUTOSE_BOT_EMAIL` | identity used for commits and the human-commit guard | `github-actions[bot]` |
| `GITHUB_REPOSITORY` | `owner/repo` passed to every `gh --repo` | `vishesh312/tinydb` |

## Syncing to the fork

```bash
git clone git@github.com:vishesh312/tinydb.git ../tinydb-fork
./sync_to_fork.sh ../tinydb-fork      # copies .autose/ and .github/workflows/, removes upstream CI/publish
cd ../tinydb-fork && git diff --stat  # review, then commit and push to main yourself
```

Repository settings that the workflows rely on: the secret `CODEX_AUTH_JSON` (the contents of your Codex ChatGPT login,
`gh secret set CODEX_AUTH_JSON --repo vishesh312/tinydb < ~/.codex/auth.json`); Issues and Actions turned on;
"Allow GitHub Actions to create pull requests" turned on; `main` protected; and optionally the variables
`AUTOSE_MODEL_*` and `AUTOSE_SANDBOX`. Run the `canary` job (Actions → autose → Run workflow) once
before the first real trigger. The workflows install the pinned `@openai/codex@0.172.0`.

> **Credential warning.** `auth.json` holds a *personal ChatGPT subscription* credential (access and refresh tokens), not a spend-capped API key. It is materialised only inside the tokenless agent steps (as `$RUNNER_TEMP/codex-home/auth.json`, mode 600, deleted by an `if: always()` step) and never sits next to `GH_TOKEN`. ChatGPT refresh tokens rotate: if a CI run refreshes the token, the copy on your machine may stop working and you will need to run `codex login` again (and then re-upload the secret). Revoke it by signing out of the session in ChatGPT settings if it may have leaked.
