# AutoSE A3: Issue in, reviewed pull request out

A GitHub Actions workflow in which agents turn a labelled issue on a tinydb fork into a tested pull request with an independent review. A human always makes the merge decision. This repository is the submission repo. The bot runs in the fork, and the fork never contains the experiment material (hidden tests, seeded-PR labels, reviewer strategy). See [ADR-012](architecture/decisions/ADR-012.md).

| | |
|---|---|
| Fork (where the bot runs) | https://github.com/vishesh312/tinydb |
| Upstream | https://github.com/msiemens/tinydb, pinned at commit **`edff96aeb2616402e9489d46e90a592c05565621`** (tinydb 4.9.0) |
| Fork `main` | the pinned upstream commit plus our setup commits: A2 `ARCHITECTURE.md`, `.autose/` (agent code and prompts, synced from `workflow/`) and `.github/workflows/`. Fork `main` head used for the first GitHub runs (13:39–13:47 UTC): `eec31b7`; for the runs after the quota reset (15:54–16:08 UTC, ADR-014 note 2 models): `0f00733` (sync PR #19), which is the current head (infrastructure syncs in between: PRs #13, #17, #18) |
| Experiment issues | [#1](https://github.com/vishesh312/tinydb/issues/1) bug, [#2](https://github.com/vishesh312/tinydb/issues/2) bug, [#3](https://github.com/vishesh312/tinydb/issues/3) feature, [#4](https://github.com/vishesh312/tinydb/issues/4) feature, [#5](https://github.com/vishesh312/tinydb/issues/5) vague. Texts are in [`experiment/issues/`](experiment/issues/) |
| Report | [`report.pdf`](report.pdf), built from [`report/report.md`](report/report.md) (8-page body + appendices; build command at the top of `report/report.md`) |
| Demo video | TODO (student): record from [`demo-script.md`](demo-script.md) and link here |

## Architecture in one paragraph

A Python orchestrator (`autose`) runs a **deterministic state machine** through the brief's six stages. It drives five agents, each a separate headless `codex exec` process (OpenAI Codex CLI on a ChatGPT subscription, [ADR-014](architecture/decisions/ADR-014.md)) with its own prompt, OS sandbox mode (read-only, or workspace-write with no network) and JSON output schema: **Analyst** (S1, uses the A1 `requirements-spec` skill, read-only), **Architect** (S2, reads the A2 `ARCHITECTURE.md`, read-only), **Developer** (S3, may write only `tinydb/**`), **Tester** (S4, a fresh context that may write only its own test file) and **Reviewer** (S6, a different model in its own tokenless job that cannot push). A single-call **Judge** checks S1 testability, and a read-only **Verifier** re-checks each blocking review finding in a fresh context before it can send work back ([ADR-015](architecture/decisions/ADR-015.md)). Release (S5) is plain code with no agent. Every stage check is a deterministic predicate (schema, AST symbol lookup, path allowlists, compile/import/mypy, full suite, and "new tests must fail on base"), and code, not an LLM, decides every transition. Across jobs, the review loop is unrolled into a fixed DAG (`gate → build → round1..3 → finalize`) so one Actions run shows the whole history. Agents hand off only schema-validated artifacts and never transcripts. The Reviewer sees only the issue, the diff and the PR-head checkout. Full design: [`architecture/DESIGN.md`](architecture/DESIGN.md).

## Deliverables map (brief's required layout)

```
README.md                         this file
report.pdf                        generated from report/report.md
report/report.md                  report source (8 pages + appendices)
demo.mp4 / link                   TODO (student): see the table above
architecture/
  DESIGN.md                       whole design in one place (summary of the ADRs)
  views/                          component view, sequence view, stage map (+ state machine)
  decisions/                      ADR-001 … ADR-015 + README.md index (ADR-011 superseded by ADR-014)
workflow/                         agent code, prompts, skill, copies of the GitHub workflows
experiment/
  issues/                         the 5 issue texts (+ maintainer answer for #5)
  hidden_tests/                   hidden acceptance tests + reference fixes (never shown to agents)
  seeded_prs/                     5 reviewer-calibration PRs (diffs + labels + friendly context)
  variants.md                     what each decision-experiment variant changes
results/
  results.csv                     per-run metrics
  runs.md                         links to every Actions run, PR and review
  tokens.md                       token and cost totals
```

| Deliverable | Link |
|---|---|
| Component view | [`architecture/views/component-view.md`](architecture/views/component-view.md) ([png](architecture/views/component-view.png)) |
| Sequence view | [`architecture/views/sequence-view.md`](architecture/views/sequence-view.md) ([png](architecture/views/sequence-view.png)). The real run for issue #1 (Actions run 45405751306, PR #14), including the quota-failed review and the `awaiting-human` fail-safe |
| Stage map (agent, artifact and check per stage) | [`architecture/views/stage-map.md`](architecture/views/stage-map.md) |
| State machine | [`architecture/views/state-machine.png`](architecture/views/state-machine.png) (source `.mmd`) |
| ADR index and summary table | [`architecture/decisions/README.md`](architecture/decisions/README.md) |
| ADRs (15: D1–D10 in ADR-001…010, plus 5 extra; ADR-011 superseded by ADR-014) | [`architecture/decisions/`](architecture/decisions/) |
| Orchestrator code, code-to-design map | [`workflow/README.md`](workflow/README.md), [`workflow/autose/`](workflow/autose/) |
| Prompts and A1 skill | [`workflow/prompts/`](workflow/prompts/) ([README](workflow/prompts/README.md)), [`workflow/skills/requirements-spec/SKILL.md`](workflow/skills/requirements-spec/SKILL.md) |
| GitHub workflows (copies of the fork's `.github/workflows/`) | [`workflow/github-workflows/`](workflow/github-workflows/): `autose.yml`, `autose-round.yml`, `ci.yml` |
| Issues | [`experiment/issues/`](experiment/issues/) |
| Hidden tests | [`experiment/hidden_tests/`](experiment/hidden_tests/) |
| Seeded PRs | [`experiment/seeded_prs/`](experiment/seeded_prs/) |
| Experiment variants (E1 tests ADR-008, E2 tests ADR-001) | [`experiment/variants.md`](experiment/variants.md) |
| Results | [`results/results.csv`](results/results.csv), [`results/runs.md`](results/runs.md), [`results/tokens.md`](results/tokens.md) |

## Models

From [DESIGN §7](architecture/DESIGN.md#7-models-adr-006-amended-by-adr-014), [ADR-006](architecture/decisions/ADR-006.md) (as amended) and [ADR-014](architecture/decisions/ADR-014.md). Harness: OpenAI Codex CLI pinned to `@openai/codex@0.172.0`, authenticated with a ChatGPT subscription (`AUTOSE_BACKEND=codex`). It supersedes the Claude Code CLI on the Anthropic API of [ADR-011](architecture/decisions/ADR-011.md), which stays selectable with `AUTOSE_BACKEND=claude`. Each role's model can be overridden with a repository variable `AUTOSE_MODEL_<ROLE>`, and its backend with `AUTOSE_BACKEND_<ROLE>`.

| Role | Stage | Model | Effort | Per-call cap (notional $) |
|---|---|---|---|---|
| Analyst | S1 | `gpt-6.1-terra` | medium | $0.75 |
| Judge (single call, no tools) | S1 check | `gpt-6.1-terra` | low | $0.05 |
| Architect | S2 | `gpt-6.1-terra` | medium | $0.75 |
| Developer | S3 | `gpt-6.1-terra` | high | $1.50 |
| Tester | S4 | `gpt-6.1-terra` | medium | $1.00 |
| Release | S5 | none (deterministic code) | — | — |
| Reviewer | S6 | `gpt-6-luna` | high | $2.00 |
| Verifier (one call per blocking finding, ADR-015) | S6 | `gpt-6-luna` | medium | $0.50 |
| Friendly reviewer (E1 arm only) | — | `gpt-6.1-terra` (builder model) | high | $2.00 |
| Cross-vendor reviewer + verifier (E1 arm only, via `agy`) | — | Claude Opus 4.6 | — | — |
| Builder (E2 variant B only) | — | `gpt-6.1-terra` | high | $2.50 |

**Budget.** A subscription has no per-call price, so costs are *notional list-price-equivalent dollars* computed from each call's token counts (`NOTIONAL_PRICES` in [`workflow/autose/backends.py`](workflow/autose/backends.py)). Run cap: **$10 (notional) per run**. The orchestrator aborts before any call whose cap could exceed it, and it reserves one Reviewer cap plus one Verifier cap before it starts a rework. Codex has no per-call budget flag, so per-call caps are checked after each call (each call is bounded by a 20-minute timeout). Token counts, the real consumption, are reported in [`results/tokens.md`](results/tokens.md).

## How to trigger the workflow

All triggers are on the fork, `vishesh312/tinydb`.

| Action | Where | Effect |
|---|---|---|
| Add the label **`autose`** | an issue | Full pipeline S1 → S6 |
| Comment **`/autose`** | an issue | Full pipeline. A re-trigger starts fresh: the branch is reset from `main` and the existing PR is updated |
| Comment **`/autose`** | an AutoSE PR (branch `autose/issue-<N>`) | A new review round on the current head |
| Comment **`/autose review`** | any **same-repo** PR (used for the seeded PRs) | One review round only. The issue comes from `Closes #N` in the PR body |

**Who may trigger.** Only humans with `write`, `maintain` or `admin` permission, as returned by the collaborators permission API, not `author_association`. For a label, the user checked is the one who added it. Bots, triage and read users, and issue authors without write access are rejected with a short comment. Comments on PRs from forks are always rejected. Triggers for the same issue queue behind each other and are never cancelled ([ADR-010](architecture/decisions/ADR-010.md)).

**What you see.** A sticky status comment on the issue (stage table and links), the PR `autose/issue-<N>` with a body built from the artifacts, a trace comment holding `spec.md`/`design.md`/`test_report.md`, and the review, posted as a `COMMENT` review with `APPROVE` or `REQUEST_CHANGES` in its header plus a label. Per-stage artifacts are uploaded as workflow artifacts. Possible end states are the labels `autose:review-approved`, `autose:review-changes-requested`, `autose:awaiting-human`, `autose:needs-info` (expected for the vague issue) and `autose:failed`. **The workflow never merges.**

## Maintainer setup (one-time, on the fork)

1. **Codex login.** Install `@openai/codex@0.172.0` locally and run `codex login` with the ChatGPT account whose subscription the runs should use. This writes `~/.codex/auth.json`. There is no per-key spend limit: usage counts against the subscription's limits. Record what you used in [`results/tokens.md`](results/tokens.md).
2. **Secret.** `gh secret set CODEX_AUTH_JSON --repo vishesh312/tinydb < ~/.codex/auth.json`. No other secret is needed. GitHub access uses the job's `GITHUB_TOKEN`.
   > **Warning.** This is a personal subscription credential (with a refresh token), not a revocable spend-capped API key. The workflows write it to a mode-600 `auth.json` only inside the tokenless agent steps and delete it afterwards; it is never in a step that holds `GH_TOKEN`. ChatGPT refresh tokens rotate, so if a CI run refreshes the token your local login may need `codex login` again (and the secret re-uploading).
3. **Variables (optional).** `AUTOSE_MODEL_ANALYST`, `AUTOSE_MODEL_JUDGE`, `AUTOSE_MODEL_ARCHITECT`, `AUTOSE_MODEL_DEVELOPER`, `AUTOSE_MODEL_TESTER`, `AUTOSE_MODEL_REVIEWER` override the defaults above (the Verifier, friendly reviewer and Builder are not wired to repository variables; set `AUTOSE_MODEL_<ROLE>` in the environment for local runs). Agent commands are always sandboxed by Codex (network off); `AUTOSE_SANDBOX=1` additionally installs bubblewrap on the runner and only changes behaviour for the legacy `claude` backend.
4. **Enable Issues and Actions.** Both are off by default on forks.
5. **Workflow permissions.** Settings → Actions → General → enable **"Allow GitHub Actions to create and approve pull requests"**.
6. **Branch protection on `main`.** Require a pull request before merging and block direct pushes, so neither the bot nor a person can push to `main` directly.
7. **Create labels**: `autose`, `autose:needs-info`, `autose:failed`, `autose:awaiting-human`, `autose:review-approved`, `autose:review-changes-requested`, `seeded`.
8. **Sync the code into the fork** (this repo's `workflow/` is the source of truth):
   ```bash
   git clone git@github.com:vishesh312/tinydb.git ../tinydb-fork
   workflow/sync_to_fork.sh ../tinydb-fork   # copies .autose/ and .github/workflows/, removes upstream CI/publish
   cd ../tinydb-fork && git diff --stat      # review, then commit and push to main through a PR
   ```
9. **Canary.** Actions → `autose` → Run workflow (`workflow_dispatch`) runs the `canary` job. It first makes one trivial `codex exec --ephemeral -s read-only` call with an output schema (proving the login and structured output work), then runs the harness checks (`python -m autose canary`). Record the result in [`results/runs.md`](results/runs.md).

## Running offline tests and local experiments

The offline tests make **no model calls and no GitHub calls**. Agents are replaced by a scripted `FakeRunner`.

```bash
# a clean tinydb at the pinned commit, with its own venv (used by the checks)
git clone https://github.com/msiemens/tinydb.git /path/to/tinydb-up
cd /path/to/tinydb-up && git checkout edff96aeb2616402e9489d46e90a592c05565621
python3 -m venv .venv && .venv/bin/pip install -e . pytest pytest-cov mypy

# orchestrator unit + FakeRunner end-to-end tests
cd /path/to/autose-assignment3/workflow
python3 -m pip install jsonschema pytest pyyaml
AUTOSE_TEST_TINYDB=/path/to/tinydb-up python3 -m pytest tests -q
# (if a globally installed anyio plugin breaks pytest start-up, add: -p no:anyio)
```

Local experiments (these **do** call models and use subscription quota; see [`experiment/variants.md`](experiment/variants.md) and [`workflow/README.md`](workflow/README.md)):

```bash
PY=/path/to/tinydb-up/.venv/bin/python

# E1 (ADR-008): independent vs friendly vs cross-vendor reviewer on the 5 seeded PRs
experiment/scripts/run_e1.sh /path/to/tinydb-up $PY /path/to/e1-out            # arms: independent friendly xvendor

# E2 (ADR-001): capture frozen S1-S2 per issue, then Developer+Tester vs single Builder, then score
(cd workflow && python -m autose --home ../results/frozen-run --python $PY local \
  --issue-file ../experiment/issues/issue-1.md --repo /path/to/fresh/tinydb --stages 1-2)
experiment/scripts/run_e2.sh /path/to/tinydb-up $PY /path/to/frozen-root /path/to/e2-out
python3 experiment/scripts/score.py 1 /path/to/e2-out/wt-1-split /path/to/tinydb-up $PY

# zero-cost dry run of any command with scripted agents
(cd workflow && python -m autose --fake tests/fixtures/pop ...)
```

Hidden tests are run against a PR head as described in [`experiment/hidden_tests/README.md`](experiment/hidden_tests/README.md). Seeded PRs are opened on the fork with [`experiment/seeded_prs/open_seeded_prs.sh`](experiment/seeded_prs/open_seeded_prs.sh).

## Status (as of 2026-11-24)

What exists and has been checked:

- Design (DESIGN.md, ADR-001…013, component/sequence/state-machine views, stage map), committed before the agent code. ADR-014 (switch to the Codex subscription backend, superseding ADR-011) and ADR-015 (review verification pass) were added later, before any pipeline run.
- Orchestrator, prompts, schemas and the three workflows.
- **Offline test suite: 120 tests.** It covers a FakeRunner end-to-end run, unit tests, the Codex/agy backends, the verification pass, and hardening regression tests for the 19 findings of an independent code review. It makes no model or GitHub calls. (One test, `test_build_collect_suite_and_fails_on_base`, asserts that the shared tinydb checkout has no extra git worktrees, so it fails while E2 worktrees from `run_e2.sh` exist on the same checkout.)
- **Fork set up and protected.** The fork `main` was `b18cfe1` at setup (`edff96a`, plus `ARCHITECTURE.md`, plus `.autose/` and the workflows) and is now `0f00733` after the later syncs. `main` is protected (PR required, admins included), and the first sync after protection went through PR [#6](https://github.com/vishesh312/tinydb/pull/6). Actions is enabled, and the lean `ci.yml` passes ([run](https://github.com/vishesh312/tinydb/actions/runs/45340122654)).
- **Seeded PRs opened.** They are [#7–#11](https://github.com/vishesh312/tinydb/pulls?q=label%3Aseeded), labelled `seeded`; their reviews are logged in [`results/runs.md`](results/runs.md).
- The 5 issue texts, hidden tests and reference fixes. The hidden tests were validated locally: they fail on base and pass with the reference fixes (19/19), and the existing 228-test suite still passes.
- The 5 seeded PRs, validated locally: each applies cleanly and passes the existing suite, mypy and its own tests, and each defect is exposed by the hidden tests or the fails-on-base check as intended.

Live runs:

- [`results/runs.md`](results/runs.md) is the authoritative list of every live run (canary, pipeline, E1, E2), with links. A run that is not listed there has not happened, and no number in this repository comes from anywhere else.
- Still open for the student: the demo video. All results are filled from real, linked runs (`results/runs.md`).

## AI use

I used a coding agent (Claude Code) substantially in this assignment. This is how the work was divided.

- **Design decisions.** For each decision area (stage boundaries, checks, agent roles, models, reviewer independence, routing, budgets, security, harness), I asked the agent for options. It proposed several design options, each with its rationale and trade-offs. I compared them and chose the option that seemed most appropriate for this project. The ADRs record the options considered and why the chosen one won.
- **My own design work and review.** I worked on the design myself. I reviewed the design document (`architecture/DESIGN.md`, the views and the ADRs) and the requirements documents (the spec and design schemas, the stage checks, and the issue texts with their expected behaviour), and had them revised where they did not match what I wanted.
- **Claude Ship features.** Partway through, I proposed adopting ideas from Anthropic's Claude Ship. The agent then adapted them into the pipeline: the Find → Verify review pass, the important / pre_existing / nit severities, and maintainer review rules read only from the base branch (ADR-015). I also decided to run the agents on my existing Codex and Antigravity subscriptions instead of a paid API (ADR-014), and later to switch to smaller models to save quota.
- **What the agent produced.** Under my direction, the coding agent wrote the orchestrator code and its tests, the GitHub workflows, the agent prompts, the diagrams, the text of the ADRs, DESIGN.md, this README and the report, and the experiment material (issue texts, hidden tests, reference patches and seeded PRs). It also ran the local experiments and triggered the GitHub runs I asked for.
- **Review.** I reviewed the generated material. The coding agent was also used for a separate second-pass review of the code and documents, and the defects it found are recorded in the ADRs and `results/runs.md`.

All runs, PRs and results are real and linked from `results/runs.md`. Model usage by the workflow itself (Codex on a ChatGPT subscription, with Antigravity for some local runs; ADR-014) is reported separately in [`results/tokens.md`](results/tokens.md).
