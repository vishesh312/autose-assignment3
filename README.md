# AutoSE A3: Issue in, reviewed pull request out

A GitHub Actions workflow in which agents turn a labelled issue on a tinydb fork into a tested pull request with an independent review. A human always makes the merge decision. This repository is the submission repo. The bot runs in the fork, and the fork never contains the experiment material (hidden tests, seeded-PR labels, reviewer strategy). See [ADR-012](architecture/decisions/ADR-012.md).

| | |
|---|---|
| Fork (where the bot runs) | https://github.com/vishesh312/tinydb |
| Upstream | https://github.com/msiemens/tinydb, pinned at commit **`edff96aeb2616402e9489d46e90a592c05565621`** (tinydb 4.9.0) |
| Fork `main` | the pinned upstream commit plus our setup commits: A2 `ARCHITECTURE.md`, `.autose/` (agent code and prompts, synced from `workflow/`) and `.github/workflows/`. Fork `main` head used for the runs: `TBD(run)` |
| Experiment issues | [#1](https://github.com/vishesh312/tinydb/issues/1) bug, [#2](https://github.com/vishesh312/tinydb/issues/2) bug, [#3](https://github.com/vishesh312/tinydb/issues/3) feature, [#4](https://github.com/vishesh312/tinydb/issues/4) feature, [#5](https://github.com/vishesh312/tinydb/issues/5) vague. Texts are in [`experiment/issues/`](experiment/issues/) |
| Report | [`report.pdf`](report.pdf), built from [`report/report.md`](report/report.md) (`TBD(run)`: not generated yet) |
| Demo video | `TBD(run)`: link will be added here after a complete live run |

## Architecture in one paragraph

A Python orchestrator (`autose`) runs a **deterministic state machine** through the brief's six stages. It drives five agents, each a separate `claude -p --bare` process with its own prompt, tool allowlist and JSON output schema: **Analyst** (S1, uses the A1 `requirements-spec` skill, read-only), **Architect** (S2, reads the A2 `ARCHITECTURE.md`, read-only), **Developer** (S3, may write only `tinydb/**`), **Tester** (S4, a fresh context that may write only its own test file) and **Reviewer** (S6, a different model in its own tokenless job that cannot push). A single-call Haiku **Judge** checks S1 testability. Release (S5) is plain code with no agent. Every stage check is a deterministic predicate (schema, AST symbol lookup, path allowlists, compile/import/mypy, full suite, and "new tests must fail on base"), and code, not an LLM, decides every transition. Across jobs, the review loop is unrolled into a fixed DAG (`gate → build → round1..3 → finalize`) so one Actions run shows the whole history. Agents hand off only schema-validated artifacts and never transcripts. The Reviewer sees only the issue, the diff and the PR-head checkout. Full design: [`architecture/DESIGN.md`](architecture/DESIGN.md).

## Deliverables map (brief's required layout)

```
README.md                         this file
report.pdf                        TBD(run): generated from report/report.md
report/report.md                  report source (8 pages + appendices)
demo.mp4 / link                   TBD(run): see the table above
architecture/
  DESIGN.md                       whole design in one place (summary of the ADRs)
  views/                          component view, sequence view, stage map (+ state machine)
  decisions/                      ADR-001 … ADR-013 + README.md index
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
| Sequence view | [`architecture/views/sequence-view.md`](architecture/views/sequence-view.md) ([png](architecture/views/sequence-view.png)). This is the *planned* sequence for now. It will be replaced with a real run's sequence: `TBD(run)` |
| Stage map (agent, artifact and check per stage) | [`architecture/views/stage-map.md`](architecture/views/stage-map.md) |
| State machine | [`architecture/views/state-machine.png`](architecture/views/state-machine.png) (source `.mmd`) |
| ADR index and summary table | [`architecture/decisions/README.md`](architecture/decisions/README.md) |
| ADRs (13, covering D1–D10 plus 3 extra) | [`architecture/decisions/`](architecture/decisions/) |
| Orchestrator code, code-to-design map | [`workflow/README.md`](workflow/README.md), [`workflow/autose/`](workflow/autose/) |
| Prompts and A1 skill | [`workflow/prompts/`](workflow/prompts/) ([README](workflow/prompts/README.md)), [`workflow/skills/requirements-spec/SKILL.md`](workflow/skills/requirements-spec/SKILL.md) |
| GitHub workflows (copies of the fork's `.github/workflows/`) | [`workflow/github-workflows/`](workflow/github-workflows/): `autose.yml`, `autose-round.yml`, `ci.yml` |
| Issues | [`experiment/issues/`](experiment/issues/) |
| Hidden tests | [`experiment/hidden_tests/`](experiment/hidden_tests/) |
| Seeded PRs | [`experiment/seeded_prs/`](experiment/seeded_prs/) |
| Experiment variants (E1 tests ADR-008, E2 tests ADR-001) | [`experiment/variants.md`](experiment/variants.md) |
| Results | [`results/results.csv`](results/results.csv), [`results/runs.md`](results/runs.md), [`results/tokens.md`](results/tokens.md) |

## Models

From [DESIGN §7](architecture/DESIGN.md#7-models-adr-006) and [ADR-006](architecture/decisions/ADR-006.md). Each role can be overridden with a repository variable `AUTOSE_MODEL_<ROLE>`.

| Role | Stage | Model | Effort | Per-call cap |
|---|---|---|---|---|
| Analyst | S1 | `claude-sonnet-5-5` | medium | $0.75 |
| Judge (single call, no tools) | S1 check | `claude-haiku-5-5` | low | $0.05 |
| Architect | S2 | `claude-sonnet-5-5` | medium | $0.75 |
| Developer | S3 | `claude-sonnet-5-5` | high | $1.50 |
| Tester | S4 | `claude-sonnet-5-5` | medium | $1.00 |
| Release | S5 | none (deterministic code) | — | — |
| Reviewer | S6 | `claude-opus-5-5` | high | $2.00 |
| Friendly reviewer (E1 variant B only) | — | `claude-sonnet-5-5` | — | — |
| Builder (E2 variant B only) | — | `claude-sonnet-5-5` | — | — |

Run cap: **$10 per run**. The orchestrator aborts before any call whose cap could exceed it, and it reserves one Reviewer cap before it starts a rework. Harness: OpenAI Codex CLI pinned to `@openai/codex@0.172.0`, authenticated with a ChatGPT subscription (`AUTOSE_BACKEND=codex`; supersedes the Claude Code CLI of [ADR-011](architecture/decisions/ADR-011.md)).

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
3. **Variables (optional).** `AUTOSE_MODEL_ANALYST`, `AUTOSE_MODEL_JUDGE`, `AUTOSE_MODEL_ARCHITECT`, `AUTOSE_MODEL_DEVELOPER`, `AUTOSE_MODEL_TESTER`, `AUTOSE_MODEL_REVIEWER` override the defaults above. `AUTOSE_SANDBOX=1` turns on the agent sandbox once the canary has shown that it works on `ubuntu-latest`.
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

Local experiments (these **do** call models and cost money; see [`experiment/variants.md`](experiment/variants.md) and [`workflow/README.md`](workflow/README.md)):

```bash
cd workflow
PY=/path/to/tinydb-up/.venv/bin/python

# E1 (ADR-008): independent vs friendly reviewer on a seeded PR
python -m autose --home ../results/e1 --python $PY review-local \
  --pr-dir ../experiment/seeded_prs/SP1 --repo /path/to/tinydb-up --variant independent   # or: friendly

# E2 (ADR-001): capture frozen S1-S2, then Developer+Tester vs single Builder
python -m autose --home ../results/frozen-run --python $PY local \
  --issue-file ../experiment/issues/issue-1.md --repo /path/to/fresh/tinydb --stages 1-2
python -m autose --home ../results/e2 --python $PY local \
  --issue-file ../experiment/issues/issue-1.md --repo /path/to/fresh/tinydb \
  --stages 3-4 --freeze-dir ../results/frozen/issue-1 --variant split                     # or: single

# zero-cost dry run of any command with scripted agents
python -m autose --fake tests/fixtures/pop ...
```

Hidden tests are run against a PR head as described in [`experiment/hidden_tests/README.md`](experiment/hidden_tests/README.md). Seeded PRs are opened on the fork with [`experiment/seeded_prs/open_seeded_prs.sh`](experiment/seeded_prs/open_seeded_prs.sh).

## Status (as of 2026-11-24)

What exists and has been checked:

- Design (DESIGN.md, 13 ADRs, component/sequence/state-machine views, stage map), committed before the agent code.
- Orchestrator, prompts, schemas and the three workflows.
- **Offline test suite: 96 passed.** It covers a FakeRunner end-to-end run, unit tests, and hardening regression tests for the 19 findings of an independent code review. It makes no model or GitHub calls.
- **Fork set up and protected.** The fork `main` is `b18cfe1`: `edff96a`, plus `ARCHITECTURE.md`, plus `.autose/` and the workflows. `main` is protected (PR required, admins included), and the first sync after protection went through PR [#6](https://github.com/vishesh312/tinydb/pull/6). Actions is enabled, and the lean `ci.yml` passes ([run](https://github.com/vishesh312/tinydb/actions/runs/45340122654)).
- **Seeded PRs opened.** They are [#7–#11](https://github.com/vishesh312/tinydb/pulls?q=label%3Aseeded), labelled `seeded`, and have not been reviewed yet.
- The 5 issue texts, hidden tests and reference fixes. The hidden tests were validated locally: they fail on base and pass with the reference fixes (19/19), and the existing 228-test suite still passes.
- The 5 seeded PRs, validated locally: each applies cleanly and passes the existing suite, mypy and its own tests, and each defect is exposed by the hidden tests or the fails-on-base check as intended.

What has **not** been run yet:

- **No live runs and no model calls.** Neither the workflow on GitHub nor the local E1/E2 experiments have been run, and no canary either. Token and cost totals are therefore zero so far.
- The `CODEX_AUTH_JSON` secret is not set yet, so the canary, the pipeline runs and the reviews cannot run.
- [`results/`](results/), the report's result sections and the demo video are scaffolding, marked `TBD(run)`. Every number there will come from a real, linked run (see the honesty rule in [`results/runs.md`](results/runs.md)).

## AI use

> **TODO (student): confirm or rewrite this statement in your own words before submitting.** The course requires the ADR reasoning to be your own. State precisely which decisions you made, what you changed in the AI drafts, and how you reviewed them.

Coding agents (Claude Code) were used substantially in this assignment, under the student's direction. They drafted the orchestrator code and tests, the GitHub workflows, the agent prompts, the Mermaid diagrams, the text of the ADRs and DESIGN.md, and the experiment material (issue texts, hidden tests, reference patches, seeded PRs and their friendly-context artifacts), as well as this README and the report skeleton. The student set the design direction and the decisions, and reviewed all generated material. Model API usage *by the workflow itself* is reported separately in [`results/tokens.md`](results/tokens.md).
