# AutoSE A3 — Design Overview

This file sets out the whole architecture in one place. The ADRs in `decisions/` justify each choice, and the views in `views/` draw it. When this file and an ADR disagree, the ADR wins, and this file is updated to match.

## 0. Setting

| Item | Value |
|---|---|
| Target repo (the fork the bot works on) | `vishesh312/tinydb`, fork of `msiemens/tinydb`. Branch `main` is cut at upstream commit `edff96aeb2616402e9489d46e90a592c05565621`, plus our setup commits (`ARCHITECTURE.md` from A2, `.autose/` agent code, `.github/workflows/`). |
| Submission repo | `vishesh312/autose-assignment3` (this repo). `workflow/` is the **source of truth** for agent code and workflows, and `workflow/sync_to_fork.sh` copies it into the fork. |
| Baseline | 228 tests pass in under 1 s (pytest, py3.13, macOS). The suite is small and fast, so the whole suite can be run after every attempt. |
| Harness | Claude Code CLI in headless mode (`claude -p --bare`) called by a Python orchestrator (`autose`). |
| Models | Sonnet 5.5 for the builder roles, Opus 5.5 for the reviewer, and Haiku 5.5 for the spec-testability judge. |

## 1. Principles (each one traces to an ADR)

1. **No agent grades its own homework.** Every artifact is checked by something other than its author. The spec is checked by a separate judge and by code, the design by code, the implementation by the tester's tests and the suite, the tests by a "must fail on base" check, and everything by an independent reviewer. A human makes the final call. (ADR-001, ADR-007)
2. **LLMs produce artifacts, and code decides transitions.** A deterministic state machine owns control flow. Agents return structured JSON alongside their markdown, and the orchestrator turns that JSON into pass, fail or route decisions. (ADR-002, ADR-007)
3. **Split agents at trust boundaries, not at stage boundaries.** We give a role its own agent when it needs a different context, different permissions or independence. Stages that need no judgement (Release) have no agent at all. (ADR-001)
4. **Artifacts are the only hand-off.** No transcripts, chain of thought or "notes to the next agent" cross between agents, except for fields defined in a schema. (ADR-003)
5. **Least privilege in three layers.** (a) The job's `GITHUB_TOKEN` permissions, (b) which secrets and tokens a process can see in its environment, and (c) the agent's tool allowlist. Every agent output is also checked against a path allowlist after it runs. (ADR-005, ADR-009)
6. **Untrusted text gets to act in exactly one place.** Only the Analyst reads the raw issue in order to act on it, and it runs read-only. The Reviewer also reads the raw issue, but only to compare the PR against it, and it is read-only as well. Every write-capable agent sees only artifacts the pipeline derived from the issue. (ADR-009)

## 2. Agents and stages

| # | Stage | Executed by | Model | Artifact(s) | Check (who decides: the orchestrator, using these predicates) |
|---|---|---|---|---|---|
| 1 | Requirements | **Analyst** agent (A1 `requirements-spec` skill + issue adapter) | Sonnet 5.5 | `spec.md`, `spec.json` | `spec.json` is valid against its schema; there is ≥1 AC; every AC has given/when/then plus an observable outcome; the **Judge** (Haiku 5.5, a separate single call) rates every AC testable; there are no `blocking` open questions. If a blocking question exists, the questions are posted on the issue, the label `autose:needs-info` is added, and the run **stops** (this is the expected result for a vague issue). If testability fails, the Analyst gets one retry with the judge's reasons, and then the run stops. |
| 2 | Design | **Architect** agent (reads A2 `ARCHITECTURE.md`) | Sonnet 5.5 | `design.md`, `design.json` | `design.json` is valid; it lists ≥1 change; every `path` exists, or is marked `new`; every `symbol` marked `modify` exists in that file (found by an AST lookup); every AC maps to ≥1 change; only `tinydb/**` paths are allowed; tests belong to the Tester, and the Architect puts test guidance in `test_hooks`. On failure, the Architect gets one retry with the checker's message, and then the run stops. |
| 3 | Implementation | **Developer** agent | Sonnet 5.5 | `diff.patch`, `dev_notes.json` | The diff is non-empty; every touched path matches `tinydb/**` (the Developer may **not** touch `tests/**`, `.github/**`, `.autose/**` or packaging files); files that are not in the design are allowed but listed as a warning; `python -m compileall -q tinydb`, `python -c "import tinydb"` and `mypy tinydb` (matching upstream CI) all pass, which is what "builds" means. |
| 4 | Testing | **Tester** agent (a separate context from the Developer) | Sonnet 5.5 | `tests/test_autose_issue_<N>.py`, `test_map.json` (the orchestrator renders `test_report.md`) | The Tester may only touch `tests/test_autose_issue_<N>.py`. Every AC maps to ≥1 collected test id. The **full suite passes** (`pytest`, using the repo's `pytest.ini`, which turns on coverage only; pycodestyle is not enforced upstream) **and** `mypy tinydb tests` passes, which mirrors upstream CI's `pytest --mypy -m mypy tinydb tests`. **≥1 new test fails on the base commit**, which is our anti-vacuous-test check: the new tests are run with the implementation files reverted. If tests fail, the run goes back to stage 3 (at most 3 Developer attempts per design). After that it goes back to stage 2 once with the failure summary, and if that fails too, the run stops. The Developer can *contest* a test in `dev_notes.json`, and the Tester then re-checks that test against the spec once. A **no-progress detector** checks whether the failing test set **or** the diff hash is the same as on the previous attempt, and escalates straight away if they are. |
| 5 | Release | **Deterministic code (no LLM)** | — | `pr.md`, PR link | The branch `autose/issue-<N>` is force-pushed with lease. The PR is opened, or updated if it already exists, with a body built from the artifacts by a template. A trace comment holds `spec.md`/`design.md`/`test_report.md` in collapsed sections. CI runs as a reusable workflow on the head SHA and posts a commit status. The check passes when `gh pr view` returns `OPEN` and the CI job concludes `success`. |
| 6 | Review | **Reviewer** agent in a **separate job** with read-only permissions and no GitHub token | Opus 5.5 | `review.json` → `review.md`, posted as a PR review (event `COMMENT`, with the verdict in the header) | `review.json` is valid. `approve` must include a non-empty `checks_performed` list with ≥1 command that the reviewer actually ran. Every finding needs evidence (`file:line` + reasoning or command output). An invalid review is re-asked once, and then counts as `changes_requested` with an "invalid review" note. **Routing:** if any finding is `approach`, go to stage 2; else if any is `code`, go to stage 3; else if any is `tests`, go to stage 4. After that the pipeline runs on to stage 5, CI and review again. There can be at most **2 send-backs**. A review after the 2nd send-back is final, and the human decides. |


### 2.1 Complete routing table (resolves gaps found while drawing the views)

Every failed check has exactly one route. "Attempt" counters are per design. A new design, whether from a revisit or from an `approach` send-back, resets the Developer and Tester counters.

| Where | Failure | Route | Counter used | When the counter is exhausted |
|---|---|---|---|---|
| S1 | schema/structure invalid or judge says untestable | S1 retry with reasons | spec attempts (max 2) | stop (`autose:failed`) |
| S1 | blocking open question | stop + post questions | — | `autose:needs-info` (not a failure) |
| S2 | design check fails | S2 retry with checker output | design attempts (max 2) | stop |
| S3 | path allowlist / compile / import / mypy fails | S3 retry with the check output | Developer attempts (max 3) | design revisit if unused, else stop |
| S4 | Tester's own check fails (touched a non-test file, an AC without a test, a collection error, **no new test fails on base**) | S4 retry with checker output | Tester attempts (max 2) | stop |
| S4 | suite fails (new or existing tests) | S3 with the failing ids + output | Developer attempts | design revisit (S2 with `failure_summary.md`) if unused, else stop |
| S4 | Developer contested a test | Tester re-checks that test against the spec once | contest (max 1 per test) | the test stands |
| S3/S4 | **no progress** (same diff hash, or same failing test set, as the previous attempt) | treated as if Developer attempts were exhausted | — | design revisit if unused, else stop |
| S5 | `gh` push or PR create/update fails | retry once after 10 s | — | stop |
| S5 | CI fails on the PR head | **stop** with the CI log link in `pr.md` | — | CI runs the same commands as the local S4 check, so a CI-only failure means the environment differs (a different Python version or a flaky test). That is a human matter, not something the agent should fix. |
| S6 | invalid review (schema or evidence rules; `changes_requested` with no blocking finding; `approve` with one) | re-ask the reviewer once | — | the run ends `awaiting-human` with the note "invalid review". This is **not** an approval, and there is no category to route on (ADR-007/013). |
| S6 | `approach` finding | S2 → S3 → S4 (the Tester **regenerates** its tests, because the public API may change) → S5 → CI → review | send-backs (max 2); this does **not** use the in-build design revisit | final review only |
| S6 | `code` finding | S3 → S4 (the existing tests are **kept**; only the suite and fails-on-base are re-run) → S5 → CI → review | send-backs | final review only |
| S6 | `tests` finding | S4 (the Tester revises its file using the findings) → S5 → CI → review | send-backs | final review only |
| any | run cost cap ($8) or job timeout reached | stop | — | `autose:failed`, with the reason in the stage artifact |

`test_report.md` is **rendered by the orchestrator** from pytest's JSON/junit results, `test_map.json` and the fails-on-base results. The Tester does not write it, because a report about tests should not come from the agent that wrote them (principle 1).

Roles that are **not** agents are the gate (authorisation), Release, the Judge (one LLM call with no tools and no loop), the status reporter, and the finaliser.

## 3. Control flow

The control flow has two levels (ADR-002).

**Inside a job**, the `autose` Python state machine runs the stages and decides every transition (`next_stage = f(stage, check_result, counters)`). Each transition is appended to `ledger.jsonl`, with the fields stage, attempt, check, verdict, tokens, cost, seconds and reason.

**Across jobs**, `.github/workflows/autose.yml` is unrolled into a fixed DAG, because Actions jobs cannot form cycles:

```
gate ─▶ build(S1→S5 push+PR) ─▶ round1[ ci ─▶ review ─▶ post ] ─▶ round2[ rework ─▶ ci ─▶ review ─▶ post ] ─▶ round3[ ... final ] ─▶ finalize
```

`round2` and `round3` call the same reusable workflow `autose-round.yml`, with `if:` conditions on the previous round's `verdict` output. `rework` reruns the stage the reviewer routed to and every stage after it, up to S5. Because everything happens in one Actions run, a person can follow the whole run on a single page.

**Triggers** (ADR-010): adding the label `autose` to an issue, or commenting `/autose` on an issue, runs the full pipeline. Commenting `/autose review` on a same-repo PR runs only a review round (this is used for seeded PRs). Commenting `/autose` on an AutoSE PR runs a new review round.

## 4. Hand-offs: what each agent sees (ADR-003)

| Agent | Receives | Deliberately excluded |
|---|---|---|
| Analyst | The issue title and body, plus comments from users with write access (Q&A answers), all fenced as untrusted data; read-only repo; the A1 skill + issue adapter | `ARCHITECTURE.md` (keeps the spec independent of any solution), other issues and PRs, comments from users without write access |
| Judge | Only the AC list from `spec.json` | Everything else (so it judges testability without being influenced by the context) |
| Architect | `spec.md`; `ARCHITECTURE.md`; read-only repo. On loop-back it also gets the previous `design.md` plus `failure_summary.md` (from S4) or the `approach` findings (from S6) | The raw issue (it gets the distilled spec, which keeps untrusted text out), the Analyst transcript |
| Developer | `design.md`, `spec.md`, repo (read/write within the allowlist). On retry it also gets the failing test ids and assertion output, truncated to 4 KB, or the `code` findings | The raw issue, the Tester's reasoning, earlier Developer transcripts (every attempt starts from a fresh context, and only the facts about the last failure are passed on) |
| Tester | The ACs from `spec.md`; the "Public API / test hooks" section of `design.md`; the repo, including the implementation | `dev_notes.json` and the Developer transcript, so the tests come from the spec and not from what the implementer believes |
| Reviewer | The raw issue (fenced), `git diff base...head`, the repo checked out at the PR head, and its **own** findings from the previous round (if there is one) | `spec.md`, `design.md`, `test_report.md`, `pr.md`, all transcripts, and GitHub access |

## 5. State (ADR-004)

| Scope | Where | Why |
|---|---|---|
| Inside a job | `$AUTOSE_HOME/issue-<N>/` holds the artifacts, `ledger.jsonl` and `state.json` | Fast, and local to the job |
| Between jobs in one run | Workflow artifacts `autose-issue<N>-r<round>` (upload/download-artifact) | These are immutable for each job, re-running a job reuses them, and the reviewer job does not download them (independence). It downloads only `autose-issue<N>-review-r<k>`, its own earlier review. The `rework` job downloads the latest review artifact to get the routed findings. |
| Code | Branch `autose/issue-<N>` | This is what the human merges |
| Human-visible + durable | One sticky status comment on the issue (marker `<!-- autose:status -->`, edited in place with a stage table and links); the PR body (`pr.md`); one PR trace comment (spec/design/test report in collapsed sections); the PR review (`review.md`) | Anyone can follow the run on GitHub, and this record outlives the 90-day retention of workflow artifacts |
| Between runs | The issue thread (clarifying Q&A), labels (`autose:needs-info`, `autose:failed`, `autose:awaiting-human`), and the existing branch and PR | A re-trigger starts a **fresh** pipeline. It resets the branch from `main`, force-pushes with lease, and **updates** the existing PR instead of opening a second one |
| Not used | Artifacts committed on the branch (they would leak spec and design into the reviewer's checkout and add noise to the merge); the Actions cache (it can be evicted, and is meant for caching, not state) | |

## 6. Tools and permissions (ADR-005)

Every agent runs as `claude -p --bare --no-session-persistence --model <m> --tools <available> --allowedTools <auto-approved> --max-budget-usd <cap> --output-format json --json-schema <schema>`. The `--bare` flag means that no `CLAUDE.md`, hooks, plugins or MCP servers are auto-loaded from the repository, which matters because the PR branch is attacker-influenced. No agent has MCP, WebFetch or WebSearch.

| Agent | `--tools` (available) | Bash allowlist | Writes |
|---|---|---|---|
| Analyst | Read, Grep, Glob | — | none (the orchestrator writes the artifacts from the structured output) |
| Architect | Read, Grep, Glob | — | none |
| Developer | Read, Grep, Glob, Edit, Write, Bash | `Bash(python -m pytest *)`, `Bash(python -m mypy *)`, `Bash(python -m compileall *)`, `Bash(git diff *)`, `Bash(git status *)` | in the working tree; enforced afterwards by the path allowlist |
| Tester | Read, Grep, Glob, Edit, Write, Bash | `Bash(python -m pytest *)` | in the working tree; enforced afterwards (one test file only) |
| Reviewer | Read, Grep, Glob, Write, Bash | `Bash(python -m pytest *)`, `Bash(python <probe-dir>/*)` (scratch probes only), `Bash(git diff *)`, `Bash(git log *)`, `Bash(git show *)` | `$RUNNER_TEMP/review-probes/` only (via `--add-dir`); any change to the working tree is discarded and does not matter, because the job cannot push |

Only deterministic code ever uses GitHub, through the `gh` CLI with the job's `GITHUB_TOKEN`. `actions/checkout` runs with `persist-credentials: false`. Agent steps never receive `GH_TOKEN`/`GITHUB_TOKEN` in their environment.

Job permissions:

| Job | Permissions |
|---|---|
| gate | `issues: write`, `pull-requests: read`, `contents: read` |
| build / rework | `contents: write`, `pull-requests: write`, `issues: write` |
| ci | `contents: read`, `statuses: write` |
| review (agent) | `contents: read`, `issues: read`, `pull-requests: read`. A *prepare* step uses the token to write the issue text, the trusted comments and `git diff` to files. The *agent* step then runs with no token in its environment and reads only those files. The only artifact it downloads is the **previous round's** `review.json`, fetched by its exact name `autose-issue<N>-review-r<k>`. |
| post-review | `pull-requests: write`, `issues: write` |
| finalize | `issues: write`, `pull-requests: write` |

## 7. Models (ADR-006)

| Role | Model | Effort | Per-call cap |
|---|---|---|---|
| Analyst | `claude-sonnet-5-5` | medium | $0.75 |
| Judge | `claude-haiku-5-5` | low | $0.05 |
| Architect | `claude-sonnet-5-5` | medium | $0.75 |
| Developer | `claude-sonnet-5-5` | high | $1.50 |
| Tester | `claude-sonnet-5-5` | medium | $1.00 |
| Reviewer | `claude-opus-5-5` | high | $2.00 |

Prices per MTok (input/output) are: Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20. The run-level cap is **$8 per run**, tracked in the ledger, and the orchestrator aborts before a call that could exceed it. Every model can be changed through repository variables `AUTOSE_MODEL_<ROLE>`.

## 8. Checks (ADR-007)

| Stage | Deterministic | LLM | Final decision |
|---|---|---|---|
| 1 | schema, AC structure, no blocking questions | Haiku judge, per-AC testability | orchestrator (AND of all) |
| 2 | schema, paths exist, symbols exist (AST), AC→change coverage, path allowlist | — | orchestrator |
| 3 | path allowlist, compileall, import, mypy | — | orchestrator |
| 4 | AC→test coverage (collect-only), full suite, fails-on-base | — | orchestrator |
| 5 | PR open, CI success | — | orchestrator |
| 6 | review schema + evidence rules | Opus reviewer verdict | reviewer verdict routes the work; a **human** merges or closes |

## 9. Reviewer independence (ADR-008)

The reviewer is kept independent in five ways:

1. It runs in its own job on a fresh runner, with no build artifacts downloaded and no GitHub token.
2. It uses a different model (Opus) from the builders (Sonnet).
3. Its prompt is its own. It is adversarial: it derives the expected behaviour from the **issue** (not the spec), writes ≥3 risk hypotheses, and must run at least one probe of its own.
4. The output rules require evidence before `approve` is allowed.
5. It is **calibrated** on 5 seeded PRs whose correct verdicts we know (one correct PR, one with a missed edge case, one with the wrong approach, one with vacuous tests, and one with a subtle bug plus a prompt injection aimed at the reviewer). Approving a seeded defect counts as a measured false approval.

## 10. Safety (ADR-009)

The defences against bad input and runaway runs are:

- **Human gate.** Only users with write, maintain or admin permission can trigger a run (checked through the collaborators API, not just `author_association`). Bot senders are ignored. Comments on PRs from forks are rejected, which avoids the "pwn request" pattern of running fork code with secrets.
- **Injection.** Untrusted text is fenced and labelled as data. Agents have no network or GitHub tools. Outputs pass deterministic path allowlists (no `.github/`, `.autose/`, `pyproject.toml`, and so on). The independent reviewer sees the raw issue. `--bare` means repo `CLAUDE.md` files are not loaded.
- **Budgets.** Each call has a `--max-budget-usd` cap, each run has an $8 cap, and the provider has a hard spend limit. Attempts are capped: 2 spec attempts, 2 design attempts, 2 Tester attempts, 3 developer attempts per design, 1 design revisit, and 2 review send-backs.
- **Timeouts.** Each agent subprocess has a 20 min timeout. The build job has `timeout-minutes` 60, and the review and CI jobs 30 and 15.
- **Stuck detection.** If an attempt produces the same diff hash or the same failing test set as the previous one, the run escalates.
- **Actions limits.** PRs and pushes made with `GITHUB_TOKEN` do not trigger other workflows, so CI is called as a reusable workflow and its result is posted as a commit status. Job time is limited. The concurrency queue holds only one pending run.
- **The model key can still leak (residual risk).** "No network tools" does **not** mean "no network". The Developer, Tester and Reviewer run `pytest` and `python` on code that came, indirectly, from the issue. That code runs with `ANTHROPIC_API_KEY` in its environment, and hosted runners have outbound network access. We reduce the risk in four ways: (a) the key is a dedicated, spend-capped key that is easy to revoke; (b) runners are ephemeral; (c) `AUTOSE_SANDBOX=1` turns on Claude Code's bash sandbox (bubblewrap) with `sandbox.network.allowedDomains=[]` and `credentials.envVars` deny for `ANTHROPIC_API_KEY`, so sandboxed commands neither see the key nor reach the network; (d) a human reads the issue before triggering. Whether (c) works on `ubuntu-latest` must be checked by a canary run before we rely on it, and the result goes into ADR-009.
- **Reviewer reservation (ADR-006).** A rework only starts if one Reviewer cap ($2) still fits under the run cap after it. At $8 this usually allows only **one** send-back. We accept that for now, and will raise the cap if the ledger shows that second send-backs fix real defects. This keeps the ADR-013 rule that every head SHA a human sees has been reviewed.
- **Deadline.** No new agent call starts if fewer than 22 minutes remain before the job's `timeout-minutes`. `finalize` runs under `if: always()`, so a stop reason is always written.
- **Stale reviews.** `post-review` discards a review whose SHA is no longer the PR head.
- **Budget interplay.** The worst case under the attempt caps alone is about 3 Developer attempts × 2 designs × $1.50, plus 2 rework rounds, which is more than $8. The $8 run cap therefore binds first. This is intended: attempt caps limit *loops*, and the run cap limits *money*.
- **Human commits are protected.** Before the branch is reset on a re-trigger, the orchestrator checks for commits on `autose/issue-<N>` that the bot did not author. If there are any, it stops with a message instead of force-pushing over a person's work.
- **Failure reporting.** Every stop writes `## Stop reason` into the artifact of the stage that failed, updates the status comment, and applies a label.

### 10.1 Operational details (added after the ADR review)
- The workflow-level `permissions: {}` grants nothing, and every job declares the permissions it needs.
- Git push credentials are configured only in the release step, after all agents in that job have finished.
- `upload-artifact` uses `overwrite: true`, so that re-running a job replaces its own artifact.
- `gh` calls always pass `--repo vishesh312/tinydb`. In a fork, `gh pr create` would otherwise default to the upstream repo, which the rules forbid.
- In the fork, Issues and Actions are turned on (both are off by default for forks), and "Allow GitHub Actions to create pull requests" is enabled.
- The Claude CLI is pinned to `@anthropic-ai/claude-code@2.1.331`, with `DISABLE_UPDATES=1`.
- **Canaries** run before the first real run and are cheap, using Haiku with `--max-turns 2`. They check that `--bare` ignores a planted `CLAUDE.md`, that a denied tool really is denied, and that `structured_output` comes back in the shape we parse.

## 11. Concurrency (ADR-010)

Only real trigger events (the `autose` label, or a comment starting with `/autose`) are grouped on the issue number. Every other event is grouped on `github.run_id` and exits in the gate, so an unrelated comment cannot cancel a queued run (ADR-010). Real triggers use the workflow-level `concurrency: autose-${{ github.event.issue.number }}` and `cancel-in-progress: false`. A second trigger for the same issue therefore queues behind the first. Different issues run in parallel on separate branches, so they cannot conflict until a human merges. Downstream jobs also carry a job-level group keyed on the **canonical** issue number that the gate resolves, so a `/autose` comment on the PR and a label on the issue still serialise.

## 12. Experiments (planned)

- **E1 — ADR-008 reviewer independence.** Variant A is our reviewer (Opus, sees only the issue and diff, adversarial prompt). Variant B is a "friendly" reviewer (Sonnet, the same model as the builders, given `spec.md`, `design.md`, `dev_notes.json` and the test report, with a neutral prompt). Both run on the 5 seeded PRs plus the real AutoSE PRs. The measures are verdict accuracy against the labels, false approvals, findings that match the seeded defect, and cost.
- **E2 — ADR-001 Developer/Tester split.** Variant A is the split described above. Variant B is a single Builder agent that implements and writes its own tests in one context. To isolate the variable, both start from the same frozen `spec.md`/`design.md` for each of the 5 issues, and both run stages 3–4 locally with `autose local`. The measures are hidden-test pass rate, fails-on-base rate, the number of AC tests that the hidden tests contradict, attempts, and tokens.

## 13. Interpretations of the brief (recorded so they can be challenged)

- **"At most twice" / "two review rounds".** A round is a reviewer verdict that requests changes and the rework that follows it. After 2 rounds, a final review is still posted, so that no unreviewed code reaches the human, but that review cannot send work back.
- **Approving the PR.** A PR opened with `GITHUB_TOKEN` cannot be approved by the same identity. The verdict is therefore posted as a `COMMENT` review whose header carries `APPROVE` or `REQUEST_CHANGES`, plus a label `autose:review-approved` or `autose:review-changes-requested`. Merging is always left to the human.
- **The vague issue.** Stopping with clarifying questions counts as stage 1 *correctly failing its check*. After a maintainer answers in the thread and re-triggers, the run continues.

## 14. Artifact contracts (interfaces between agents and the orchestrator)

Agents return their final answer as JSON, enforced by `--json-schema` and validated again by the orchestrator. The orchestrator renders the `.md` artifact from the JSON, plus any free-text `*_md` field. The JSON Schemas live in `workflow/autose/schemas/<name>.schema.json`.

**spec.json** (Analyst)
```
{ "issue": int, "title": str, "summary": str,
  "issue_type": "bug"|"feature"|"vague"|"other",
  "source_excerpts": [{"id":"SRC-1","quote":str}],
  "requirements": [{"id":"REQ-1","text":str,"provenance":"STATED"|"CONFIRMED"|"DERIVED"|"ASSUMED","sources":[str]}],
  "acceptance_criteria": [{"id":"AC-1","requirement":"REQ-1","given":str,"when":str,"then":str,"observable":str}],
  "open_questions": [{"id":"Q-1","question":str,"why_it_matters":str,"blocking":bool,"options":[str],"default_if_unanswered":str|null}],
  "out_of_scope": [str], "injection_findings": [str], "spec_md": str }
```
**judge.json** (Judge): `{ "verdicts": [{"ac":"AC-1","testable":bool,"reason":str}] }`

**design.json** (Architect)
```
{ "approach": str,
  "changes": [{"path":"tinydb/queries.py","symbol":"Query.between","kind":"modify"|"new","new_file":bool,"description":str,"acs":["AC-1"]}],
  "public_api": [{"signature":str,"behaviour":str}],      // with test_hooks, the only design content the Tester receives
  "test_hooks": [str], "risks": [str], "architecture_refs": [str], "design_md": str }
```
**dev_notes.json** (Developer): `{ "summary": str, "files_changed": [str], "deviations_from_design": [str], "contested_tests": [{"test_id":str,"reason":str}], "self_check": str }`

**test_map.json** (Tester): `{ "test_file": "tests/test_autose_issue_<N>.py", "mapping": [{"ac":"AC-1","tests":["tests/...::test_ac1_..."]}], "notes": str }`

**review.json** (Reviewer)
```
{ "verdict": "approve"|"changes_requested",
  "summary": str,
  "expected_behaviour_from_issue": [str],     // derived independently by the reviewer
  "risk_hypotheses": [{"hypothesis":str,"how_tested":str,"outcome":"confirmed"|"refuted"|"untested"}],
  "checks_performed": [{"command":str,"result":str}],
  "findings": [{"id":"F-1","severity":"blocking"|"minor","category":"approach"|"code"|"tests","file":str,"line":int|null,"description":str,"evidence":str,"suggested_fix":str}],
  "injection_attempts_noticed": [str], "review_md": str }
```
**ledger.jsonl**, one line per event: `{ "ts", "run_id", "issue", "round", "stage", "attempt", "actor", "model", "event": "start"|"check"|"route"|"stop", "passed": bool|null, "reason": str, "tokens_in", "tokens_out", "cache_read", "cost_usd", "seconds" }`

**state.json**: `{ "issue", "branch", "base_sha", "head_sha", "pr", "round", "stage", "attempts": {"S1":n,...}, "design_revisits": n, "send_backs": n, "cost_usd": x, "status": "running"|"stopped"|"needs-info"|"awaiting-human", "stop_reason": str|null }`
