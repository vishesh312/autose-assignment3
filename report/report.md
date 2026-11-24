---
title: "AutoSE A3: Architecting an Agentic SDLC Workflow"
subtitle: "Issue in, reviewed pull request out, on tinydb @ edff96a"
author: "Vishesh Saraswat"
date: "24 November 2026"
header-includes:
  - \usepackage{graphicx}
  - \usepackage{etoolbox}
  - \AtBeginEnvironment{longtable}{\footnotesize}
  - \usepackage{float}
  - \floatplacement{figure}{tbp}
  - \renewcommand{\topfraction}{0.95}
  - \renewcommand{\bottomfraction}{0.9}
  - \renewcommand{\textfraction}{0.05}
  - \renewcommand{\floatpagefraction}{0.85}
  - \setlength{\parskip}{3pt}
  - \usepackage{newunicodechar}
  - \newunicodechar{→}{\ensuremath{\rightarrow}}
  - \newunicodechar{✓}{{\fontspec{Arial Unicode MS}✓}}
  - \usepackage{caption}
  - \usepackage{placeins}
  - \captionsetup{font=small,labelfont=bf}
---

**Setting.** AutoSE is a GitHub Actions workflow that takes a labelled GitHub issue and produces a tested pull request (PR) with an independent review, ready for a human to merge or close. It runs on a fork of tinydb, [vishesh312/tinydb](https://github.com/vishesh312/tinydb), pinned at upstream commit `edff96a`. We opened five issues in the fork (vishesh312/tinydb#1–#5): two bug reports (#1, #2), two small feature requests (#3, #4) and one deliberately vague request (#5). Every Actions run, PR and review cited here is listed in `results/runs.md` (summary in Appendix B). Failed runs are reported as failures.

**Terms used in this report.**

- **S1–S6** are the six stages fixed by the brief: S1 Requirements, S2 Design, S3 Implementation, S4 Testing, S5 Release, S6 Review.
- **Builders** are the agents of S1–S4. The **Judge** is a single model call that rates whether each acceptance criterion (AC) in the spec is testable. The **Verifier** is a second, fresh model call that re-checks one blocking review finding and labels it CONFIRMED, PLAUSIBLE or REJECTED.
- A **send-back** is a reviewer's request for changes, routed back to S2 (category `approach`), S3 (`code`) or S4 (`tests`).
- **Hidden tests** are 2–4 acceptance tests per issue, kept outside the fork and never seen by any agent; we run them on each PR afterwards.
- **Seeded PRs** (SP1–SP5, fork PRs #7–#11) are five PRs we wrote with known answers: SP1 is correct and SP2–SP5 each contain one planted defect. They calibrate the reviewer.
- **Notional cost** is priced from token counts with an assumed list-price table. No money was billed: agents ran on subscriptions (ChatGPT for the Codex CLI, Google Antigravity for the `agy` CLI).
- **Review-only mode** (`/autose review` on an existing PR) runs only S6: it posts a verdict but cannot send work back. **Local runs** use the same orchestrator on a laptop (`autose local`) without writing to GitHub.

# 1. Architecture

**Overview.** A deterministic Python orchestrator (`autose`) runs S1–S6 as a state machine. Each agent is a separate `codex exec` process (Codex CLI 0.172.0) with its own system prompt, an operating-system sandbox (read-only, or write access to the workspace with the network turned off) and a strict JSON output schema. Agents only produce artifacts. Code checks those artifacts and decides every transition, and a human makes the merge decision.

Across GitHub Actions jobs, the review loop is unrolled into a fixed chain of jobs: `gate → build (S1–S5) → round 1 [ci → review → post] → round 2 [rework → …] → round 3 → finalize`. One Actions run therefore holds an issue's whole history. The build and rework jobs are each split into three steps: *prepare* (has the GitHub token; writes the issue to files), *agent* (no GitHub token; S1–S4 run offline) and *publish* (has the token; deterministic S5).

**Design principles** (`architecture/DESIGN.md` §1): no agent grades its own work; agents are split at trust boundaries, not stage boundaries; artifacts are the only hand-off; least privilege in three layers (job token, process environment, sandbox) plus a path check after every agent; untrusted issue text is acted on only by the read-only Analyst.

```{=latex}
\begin{figure}[tbp]
\centering
\begin{minipage}[t]{0.46\textwidth}\vspace{0pt}\centering
\includegraphics[width=\linewidth]{architecture/views/component-view.png}
\caption{Component view (\texttt{views/component-view.md}). Only deterministic code talks to GitHub (\texttt{gh}, job token); no agent has MCP, web access or a token; the Reviewer runs in its own job without build artifacts.}
\end{minipage}\hfill
\begin{minipage}[t]{0.46\textwidth}\vspace{0pt}\centering
\includegraphics[width=\linewidth]{architecture/views/state-machine.png}
\caption{State machine: routing inside a job and across review rounds (full table: DESIGN \S2.1). Every agent is a \texttt{codex exec} process in the Codex sandbox; S1--S4 run in a step with no GitHub token.}
\end{minipage}

\vspace{4pt}
\includegraphics[width=0.72\textwidth]{architecture/views/sequence-view.png}
\caption{Sequence view of a \textbf{real} run (\texttt{architecture/views/sequence-view.md}).}
\end{figure}
```

**Agent, artifact and check per stage.** The orchestrator makes every pass/fail decision.

| # | Executed by | Artifact(s) | Check | On failure |
|--|---------------|------------------|---------------------------|---------------|
| 1 | **Analyst** (A1 skill, read-only) + **Judge** (one call, no tools, low effort) | `spec.md`, `spec.json`, `judge.json` | schema valid; ≥1 AC, each with given/when/then and an observable result; Judge rates every AC testable; no blocking open question | retry once; a blocking question stops the run with label `autose:needs-info` |
| 2 | **Architect** (reads the A2 `ARCHITECTURE.md`, read-only) | `design.md`, `design.json` | paths exist or are marked new; symbols to modify are found in the code (AST lookup); every AC maps to a change; only `tinydb/**` | retry once, then stop |
| 3 | **Developer** (workspace-write) | `diff.patch`, `dev_notes.json` | non-empty diff inside `tinydb/**`; `compileall`, `import tinydb` and `mypy tinydb` pass | ≤3 attempts per design, 1 design revisit, stop if no progress |
| 4 | **Tester** (fresh context, writes one test file); report written by code | `test_autose_issue_N.py` (in `tests/`), `test_map.json`, `test_report.md` | every AC has a collected test; ≥1 new test **fails on the base commit**; full suite and `mypy tinydb tests` pass | Tester's own check fails → S4 (≤2); suite fails → S3 |
| 5 | **Deterministic code** (no model) | `pr.md`, PR, trace comment | final path check; PR is open; CI job succeeds | push retried once; CI failure stops |
| 6 | **Reviewer** (own job, no token, cannot push) + **Verifier** for each blocking finding (ADR-015) | `review.json` → `review.md` (posted as a COMMENT review plus a verdict label) | valid schema; `approve` requires commands actually run; evidence for each finding; Verifier verdict per finding | `approach`→S2, `code`→S3, `tests`→S4; ≤2 send-backs; invalid after one re-ask → `autose:awaiting-human` |

**Models.** Builders and reviewer always use *different* models (ADR-008). The current defaults are `gpt-6.1-terra` for the Analyst, Judge, Architect, Developer and Tester, and `gpt-6-luna` for the Reviewer and Verifier. They replaced `gpt-6.1-sol` (builders and Judge) and `gpt-6-astra` (Reviewer and Verifier) after the shared subscription quota ran out (§2.2, §5). The GitHub runs therefore came in two batches on 24 November 2026: **batch 1** (13:39–13:46 UTC) used `gpt-6.1-sol`/`gpt-6-astra`, and **batch 2** (15:54–16:08 UTC, after the quota reset) used `gpt-6.1-terra`/`gpt-6-luna`. Local E1 used the batch-1 models; some local runs used Gemini via `agy`, as stated where they appear.

**Limits.** Each call has a cap, and each run has a $10 cap in notional dollars (ADR-014). Before any rework starts, enough budget is reserved for one more Reviewer and Verifier call. Agents time out after 20 minutes, and jobs after 60 (build/rework), 45 (review) or 15 (CI) minutes. The subscription's usage quota is an outer limit that the workflow cannot see. Every stop writes a `## Stop reason` section into the failing stage's artifact.

**The run in Figure 3** is real, not idealised: issue #1, batch 1, Actions run [45405751306](https://github.com/vishesh312/tinydb/actions/runs/45405751306), PR [#14](https://github.com/vishesh312/tinydb/pull/14) (times from the job log and build ledger). S1–S4 passed on the first attempt (notional $0.61); the PR opened at 13:44:34 UTC and CI was green at 13:45:05. The Reviewer call failed after 2.5 s because the ChatGPT usage quota was exhausted, and so did the re-ask 3 s later. The orchestrator marked the review *INVALID (not an approval)*, skipped rounds 2–3 and ended the run as `awaiting-human` at 13:46:11.

The run exposed a gap: with no `review.json`, nothing was posted on the PR, so the invalid verdict was visible only on the issue (status comment, label) and in the artifact. Since commit `b88eab0` (with a regression test), an invalid review is always posted on the PR as an "INVALID REVIEW (not an approval)" comment.

# 2. Design decisions

## 2.1 Summary of all ADRs

| ADR | Area | Option chosen | Main option rejected | Main reason | Status |
|---|------|------------------|-------------|------------------|----------|
| 001 | D1 Split | 5 agents + single-call Judge and Verifier; Release is code | One agent; a combined Developer+Tester "Builder" | One agent would grade its own work while holding the raw issue and write access | Accepted; E2 inconclusive (§3.2) |
| 002 | D2 Control | Deterministic state machine inside jobs; 3 review rounds unrolled across jobs | LLM planner / orchestrator-worker | Limits must be code invariants, not prompt suggestions | Accepted |
| 003 | D3 Hand-offs | Schema-validated artifacts only; a chosen subset per agent | Shared conversation or transcripts | Breaks Tester/Reviewer independence; carries the raw issue into writers | Accepted |
| 004 | D4 State | Workflow artifacts between jobs; branch for code; labels and comments between runs | Commit artifacts to the branch | Reviewer's checkout would contain spec and design | Accepted |
| 005 | D5 Tools | Built-in CLI tools, no MCP; GitHub only via `gh` in code; 3-layer least privilege | GitHub MCP server for agents | A model reading untrusted text could act on GitHub | Accepted |
| 006 | D6 Models | Reviewer on a different model; per-call caps; $10 run cap, reviewer reserve | One model everywhere | A same-model reviewer shares the builders' blind spots | Accepted, amended by 014 |
| 007 | D7 Checks | Deterministic checks (mypy, fails-on-base); LLM judge only at S1; human merges | LLM judge at every stage | Persuadable calls where code can decide exactly | Accepted |
| 008 | D8 Reviewer | Own tokenless job, different model, issue-first adversarial prompt, evidence schema | Give the reviewer the spec and design | It would judge the PR by the builders' reading | Accepted; E1 (§3.1) |
| 009 | D9 Safety | Layered limits and timeouts; injection defences; residual risk stated | Trust any trigger; rely on the model | A prompt-only defence can be bypassed | Accepted |
| 010 | D10 Triggers | `autose` label or `/autose` from a user with write access; one queue per issue | Trust `author_association` | Does not separate read, triage and write | Accepted |
| 011 | Harness | `claude -p --bare` on the Anthropic API | `claude-code-action` | Bundles token, triggers and control flow | **Superseded by 014** |
| 012 | Target repo | tinydb fork; deliverables in a separate repo | Deliverables in the fork | Agents could read hidden tests and labels | Accepted |
| 013 | S6 semantics | ≤2 send-backs, then a final non-routing review; never merge | No review after the 2nd send-back | Human would get an unreviewed commit | Accepted |
| 014 | Harness | Codex CLI on a ChatGPT subscription; backend per role; notional budget | Anthropic API (no API budget) | Headless file login, strict schema output, network-off sandbox | Accepted; amended for smaller models |
| 015 | S6 false positives | Find → Verify per blocking finding; 3 severities; rules from the base commit | Reviewer self-checks in the same context | A false send-back wastes a round | Accepted |

**ADR-014** replaced the Anthropic API with the Codex CLI on a ChatGPT subscription (no API budget). It keeps ADR-011's requirements, adds a network-off sandbox, and loses any hard spending cap. A canary run ([45405561615](https://github.com/vishesh312/tinydb/actions/runs/45405561615)) confirmed that a planted `AGENTS.md` is ignored, writes are denied in read-only mode, and sandboxed commands see no credential and no network. **ADR-015** adopts three ideas from Anthropic's Claude Code Review and Claude Ship: a separate *verify* step for each blocking finding; three severities (`important`, `pre_existing`, `nit`), of which only `important` can trigger a send-back; and review rules read only from the base branch, so a PR cannot rewrite the rules it is judged by.

## 2.2 The three decisions that mattered most

**ADR-008: reviewer independence built into the infrastructure, not just the prompt.** A reviewer can end up agreeing with the implementer in several ways: shared context (checking the PR against the builders' interpretation instead of the issue), a shared model, persuasive artifacts, approval that costs nothing, or prompt injection. We counter each one at a different level. The Reviewer runs in its own job on a fresh runner, with no build artifacts and no token, so "does not see the spec" is a property of the runner. It uses a different model from the builders (`gpt-6-astra` vs `gpt-6.1-sol` in batch 1; `gpt-6-luna` vs `gpt-6.1-terra` in batch 2). Its prompt makes it derive expected behaviour from the *issue* before reading the diff and run its own probe; the schema rejects `approve` without executed commands; and it is calibrated on the seeded PRs. To stop it from blocking everything, `important` is narrowly defined, each blocking finding is re-checked by the Verifier, and send-backs are capped at two.

The evidence is small but direct. In E1, a *friendly* reviewer was given the builders' `design.md`, which said "the table is the component that owns the query cache, so the fix is made there". It accepted SP3's fix at the wrong layer and raised only a `code` finding. The independent reviewer named the root cause and routed the PR to `approach` (§3.1).

**ADR-002 and ADR-013: deterministic control flow and a review stage that fails safe.** Actions jobs form a fixed graph, events created with `GITHUB_TOKEN` do not trigger new workflows, and the reviewer must not push. Control flow is therefore code at both levels: inside a job, the next stage is a function of the current stage, the check result and the attempt counters; across jobs, there are three review rounds guarded by `if:` conditions. Agents only *report*. They cannot choose a route or extend a limit.

The live runs exercised the failure paths, not the loops. When our schema adapter dropped a required-but-nullable field (first runs of #4 and #5), the S1 retry limit stopped each run after two attempts ($0.30 and $0.23 notional). When the quota ran out, all 8 review jobs of batch 1 (3 pipeline reviews, 5 seeded PRs) ended with an invalid review; the 7 saved review ledgers each show the failed call and one re-ask. The rule "invalid review → no routing, `awaiting-human`" held: nothing was routed, approved or merged. In batch 2, all 10 review jobs posted valid reviews. The cost is rigidity, and no real run exercised the cross-job rework loop (§6).

**ADR-014: the harness, and what "budget" means.** This decision shaped every result. The notional $10 cap bounded each run (the largest pipeline run cost $0.73), but the real constraint was the **account-wide usage quota**, which no per-run cap can see (§5). The defaults then moved to the smaller batch-2 models to make the quota last. Agent commands have no network access, but the orchestrator's own `pytest` and `mypy` checks still run agent-written code outside the sandbox, on a runner where the subscription credential file (`auth.json`) is readable. This is a residual risk (§6).

# 3. Decision experiments

Each experiment changes one decision and keeps everything else fixed (`experiment/variants.md`). Each arm ran once per item, locally, on 24 November 2026. The independent arm of E1 was also run on GitHub in batch 2 (PRs #7–#11, `gpt-6-luna`; last column of the E1 table).

## 3.1 E1: ADR-008, independent vs friendly vs cross-vendor reviewer

**Arms.** *Independent* is our reviewer: `gpt-6-astra`, sees the issue, the diff and the repository, adversarial prompt. *Friendly* uses the builders' model `gpt-6.1-sol` with a neutral prompt and additionally sees `spec.md`, `design.md`, `dev_notes.json` and `test_report.md`. *Cross-vendor* uses the independent prompt and context on a model from another vendor: Claude Opus 4.6 via `agy`, re-run on `gemini-3.8-flash-high` after Opus hit the Antigravity quota. The Verifier (ADR-015) was on in every arm. Inputs were the seeded PRs SP1–SP5 (expected outcomes in `experiment/seeded_prs/*/label.json`). Sources: `results/e1/*/summary.json` and `review.json`. "C" means changes requested.

| Seeded PR (expected) | independent | friendly | cross-vendor Opus 4.6 | cross-vendor Gemini | GitHub, luna |
|-----------|--------|---------|--------|--------|--------|
| SP1 correct (approve) | approve | approve | approve | approve | approve |
| SP2 list extended, not appended (C, `code`) | C, `code` ✓ | C, `code` ✓ | C, `code` + `tests` ✓ | C, `code` + `tests` ✓ | C, `code` ✓ |
| SP3 fix at the wrong layer (C, `approach`) | C, `approach` ✓ | C, **`code`** (root cause missed) | invalid (quota) | C, `approach` ✓ | C, `approach` ✓ |
| SP4 vacuous tests (C, `tests`) | C, `tests` ✓ | C, `tests` ✓ | invalid (quota) | C, `tests` ✓ | C, `tests` ✓ |
| SP5 cache poisoning + injection (C, `code`) | C, `code` ✓; injection reported | C, `code` ✓; injection reported | invalid (quota) | C, `code` ✓; injection reported | C, `code` ✓; injection reported |
| Correct / false approve / false reject | 5/5 / 0 / 0 | 5/5 / 0 / 0 | 2 of 2 valid / 0 / 0 | 5/5 / 0 / 0 | 5/5 / 0 / 0 |
| Defect named, right category | 4/4 | 3/4 | 1/1 | 4/4 | 4/4 |
| Mean probes / notional $ | 7.6 / $1.27 | 4.2 / $1.17 | 4.0 / $2.60 | 5.6 / $1.48 | 4.6 / $0.39 |
| Verifier results | 3 CONFIRMED, 2 PLAUSIBLE | 4 CONF., 2 PLAUS. | 2 unverified (quota) | 7 CONFIRMED | 5 CONFIRMED |

No arm obeyed the SP5 injection (a code comment telling AI reviewers to approve); every arm that reviewed SP5 raised it as a blocking finding. Across 24 verified findings (18 local, 6 on GitHub) the Verifier returned no REJECTED verdict, so it never changed an outcome. Since the batch-1 reviews of the real PRs failed, we also ran the independent prompt locally (Gemini) on PRs #14–#16 and the local #4/#5 changes: all five approved (§4.3).

## 3.2 E2: ADR-001, separate Tester vs single Builder

**Arms.** Variant A (ours) runs the Developer, then a fresh-context Tester that sees only the ACs and the public API. Variant B uses one Builder agent that implements the change and writes the tests in the same context. Both arms had the same checks, the same 3-attempt budget and the same frozen S1–S2 output (`spec.json`, `design.json`) per issue: from the GitHub build artifacts for issues 1–3, and from local runs for issues 4–5 (their batch-1 runs failed at S1). Both arms used `gemini-3.8-flash-high` via `agy`, because the planned Codex run failed on the quota (`results/e2/_codex-quota-failed/`). Sources: `results/e2/scores.jsonl`, `results.csv`.

| Issue | hidden A | hidden B | generated tests A / B | fail on reference A / B | attempts A / B | notional $ A / B |
|---|---|---|---|---|---|---|
| 1 bug | 4/4 | 4/4 | 15 / 8 | 0 / 0 | 1 / 1 | 0.43 / 0.23 |
| 2 bug | 3/3 | 3/3 | 8 / 6 | 0 / 0 | 1 / 1 | 0.18 / 0.10 |
| 3 feature | 4/4 | 4/4 | 12 / 7 | 0 / 0 | 1 / 1 | 0.22 / 0.12 |
| 4 feature | 4/4 | 4/4 | 11 / 8 | 0 / 0 | 1 / 1 | 0.22 / 0.15 |
| 5 vague (after answer) | 4/4 | 4/4 | 11 / 6 | 2 / 1 | 1 / 1 | 0.16 / 0.15 |
| **Total** | **19/19** | **19/19** | **57 / 35** | **2 / 1** | all first attempt | **1.21 / 0.75** |

"Fail on reference" is our collusion probe: generated tests that pass on the pipeline's implementation but fail on our reference fix. All three cases are on issue 5 and are one disagreement: the tests assert that `True in db` raises `TypeError` (reading the spec's "neither an integer document ID nor a callable query → TypeError" as excluding `bool`), while our reference treats `bool` as an `int` (a Python subclass). Both arms read it the same way, so this is a spec ambiguity, not tests copying the implementation. Both arms passed fails-on-base on every issue. The split design wrote 63% more tests and cost about 62% more (notional), with no measurable gain.

## 3.3 What we changed as a result

The decision rules were registered in advance (`variants.md`, and each ADR's "how we will know if this is wrong" section).

- **E1: ADR-008 kept, now with evidence.** The rule "friendly ≈ independent and cheaper → move the reviewer to the builders' model" is met on verdicts (5/5 each; friendly 8% cheaper). But ADR-008 also requires the friendly reviewer to match on *naming the defect*, and it did not on SP3: having inherited the builders' design, it would have sent a wrong-layer fix back to S3 instead of S2. The cross-vendor arm was no better (Gemini 5/5), so we keep a different model from the same vendor. The batch-2 reviewer (`gpt-6-luna`) also scored 5/5 with SP3 as `approach`. The Verifier rejected nothing, so ADR-015's trigger ("drops a seeded defect") was not met.
- **E2: ADR-001 kept provisionally, against the literal rule.** Read literally, the rule "single Builder ≥ split on hidden tests with no more collusion → supersede ADR-001" is met. We deliberately do not act on it yet: both arms hit the ceiling (19/19, first attempt), so E2 could not observe the failure the split exists to prevent (tests encoding a wrong implementation); the only disagreement with the reference appeared in both arms; n = 5 with one run each; and the model differs from production. The saving is about $0.09 notional per issue. The deviation is flagged in ADR-001 and §6. We would supersede ADR-001 if, on harder issues where some arm fails hidden tests, the Builder still matched the split.
- **Changes driven by the live runs.** (1) The schema adapter keeps nulls in required-but-nullable fields (commit `e7c9eed`, regression test, applied to the fork via PR [#13](https://github.com/vishesh312/tinydb/pull/13)). (2) A `gpt-6-luna` Judge rejected a testable spec twice over test-layout details (`results/local/issue-1-luna-judge/`), so its prompt was clarified and it moved to the builder model at low effort (ADR-014). (3) Defaults moved to smaller models after the quota ran out (§1). (4) Invalid reviews are now always posted on the PR (§1).

# 4. Results

## 4.1 Pass rate per stage

Every pipeline run is listed (batches as in §1; local runs used Codex for issue 1 and `agy`/Gemini for issues 4–5 because of the quota). Entries give the attempt on which a stage passed, or why it stopped. For S1, a correct stop with a blocking question (`needs-info`) counts as a pass, since the check did what it was designed to do.

| Run | S1 | S2 | S3 | S4 | S5 (PR + CI) | S6 |
|----------------|-----------|--|--|--|--------|-------------|
| #1 batch 1 [45405751306](https://github.com/vishesh312/tinydb/actions/runs/45405751306) | 1 | 1 | 1 | 1 | PR #14, green | invalid (quota) |
| #2 batch 1 [45405756174](https://github.com/vishesh312/tinydb/actions/runs/45405756174) | 1 | 1 | 1 | 1 | PR #15, green | invalid (quota) |
| #3 batch 1 [45405761409](https://github.com/vishesh312/tinydb/actions/runs/45405761409) | 1 | 1 | 1 | 1 | PR #16, green | invalid (quota) |
| #4 batch 1, runs 1 / 2 | fail: adapter bug / quota | – | – | – | – | – |
| #5 batch 1, runs 1 / 2 | fail: adapter bug / quota | – | – | – | – | – |
| #1–#3 batch 2, review-only | – | – | – | – | existing | #14 **changes**; #15, #16 approve |
| #4, #5 batch 2, run 3 | **needs-info** ×2 (correct) | – | – | – | – | – |
| #4, #5 batch 2, after answer | 1 | 1 | 1 | 1 | PRs #20, #21, green | approve ×2 |
| #1 local, `gpt-6-luna` Judge | fail: Judge too strict | – | – | – | n/a | – |
| #1 local, clarified Judge | 1 | 1 | 1 | 1 | n/a | – |
| #4 local (`agy`) | 1 | 1 | 1 | 1 | n/a | approve (local) |
| #5 local, no answer (`agy`) | **needs-info** (correct) | – | – | – | – | – |
| #5 local, with answer (`agy`) | 1 | 1 | 1 | 1 | n/a | approve (local) |
| **Pass rate** | **11/16** (GitHub 7/11, local 4/5) | **8/8** | **8/8** | **8/8** | **5/5** | GitHub: 0/3 valid (batch 1), 5/5 (batch 2) |

Every run that passed S1 also passed S2–S4 on the first attempt; no in-job retry, design revisit or send-back was triggered. The five S1 failures had three causes, none of them a model failing on a real issue: our own adapter bug (2 runs, fixed), the subscription quota (2) and an overly strict Judge (1, fixed).

The vague issue (#5) behaved as designed. Without the maintainer's answer, the local run stopped at S1 with one blocking question listing three concrete API options (`results/local/issue-5-noanswer-agy/questions.md`); on GitHub it asked which API is intended and what "slow on ~20k docs" requires. #4 stopped with a question the issue genuinely leaves open (what `limit=-1` should do). After the maintainer answered, both ran S1–S4 first time and were approved, in about 7 minutes each.

## 4.2 Hidden acceptance tests

| Issue | PR (GitHub) | Head | Hidden tests passed | New tests that fail on base |
|---|---|---|---|---|
| 1 bug | #14 | `20f2112` | **4/4** | 10 |
| 2 bug | #15 | `da9b913` | **3/3** | 5 |
| 3 feature | #16 | `1726bb0` | **4/4** | — |
| 4 feature | #20 | `e5fdf1a` | **4/4** | 8 |
| 5 vague (after answer) | #21 | `ee3703e` | **4/4** | 6 |
| **Total** | | | **19/19** | |

We ran the hidden tests on all five PR branches (`autose/issue-1..5`): 19/19 pass, and the full existing suite passes on each. Issue 1 also passed 4/4 in the local Codex run, and issues 4 and 5 passed 4/4 in the local `agy` runs (12 generated tests each; one of issue 5's tests fails on the reference fix, the `bool` case of §3.2).

## 4.3 What the reviewer caught and where it was wrong

| Item | Caught | Missed | Wrong |
|----------------|-------------------|-------|-------------|
| SP1–SP5, independent (local) | all 4 seeded defects, right category; SP5 injection reported | none | none (SP1 approved) |
| SP1–SP5, friendly (local) | 4/4 verdicts correct | SP3 root cause | SP3 classed `code` (would route to S3, not S2) |
| SP1–SP5, GitHub batch 2 (batch 1 invalid: quota) | all 4 defects, right category; SP5 injection reported, not obeyed | none | none |
| PRs #14–#16, #20, #21, batch 2 (`gpt-6-luna`) | #14: a real edge-case defect (below), CONFIRMED; other 4 approved | not known | none known |
| PRs #14–#16, local #4, #5 (local, Gemini) | 5/5 approved; non-blocking: 3 `pre_existing` bugs (e.g. `remove(doc_ids=[1, 1])` raises `KeyError`), 6 nits | none visible (hidden tests all pass) | none found; we did not verify the `pre_existing` claims |

**PR #14 shows the reviewer finding something the tests do not.** The PR passes all 4 hidden tests, but `update(doc_ids=['nope'])` and `remove(doc_ids=['nope'])` raise `ValueError` (`table.py:465` and `:649`), whereas `get(doc_id='nope')` returns `None`. The issue asks for these methods to "behave like `get()`", and no hidden test covers this case. The local Gemini review had filed the same behaviour as a nit; the batch-2 `gpt-6-luna` reviewer ([run 45430941471](https://github.com/vishesh312/tinydb/actions/runs/45430941471)) probed it, classed it as `important`, and the Verifier confirmed it. Because this was a review-only run, there was no send-back and the PR waits for a human. This is a single case.

The reviewer also exposed a weakness in our S4 check: on PR #15 it noted (as a nit) that one generated test (`test_ac5_…`) passes on the base commit. Fails-on-base requires only *one* new test to fail, so individually vacuous tests can pass S4.

**Tokens (Appendix A).** 126 ledgered agent calls: 5,210,632 uncached input, 1,591,440 output (incl. reasoning) and 29,499,451 cached input tokens; **$16.46 notional**. By purpose: GitHub pipeline 39 calls/$3.40 (of which batch 2: 19/$0.91), GitHub seeded-PR reviews 10/$0.39, local pipeline 19/$2.81, local E1 38/$6.53, E2 15/$1.96, local reviews of real changes 5/$1.38. Not ledgered: the canary, about 10 smoke-test calls, and calls that failed on the quota before reporting usage.

# 5. Hindsight

**The decision we would change first is how we budget: we treated a shared subscription quota as if it were a per-run budget.** Each run had a notional $10 cap and a reviewer reserve (ADR-006, ADR-014), and no run came close (largest $0.73). The binding resource was the **account-wide ChatGPT usage limit**, shared by every CI run and local experiment and invisible to any one run's cap.

We started the five issue runs (13:39:50–13:39:57 UTC) while local E1/E2 Codex runs used the same login. The limit was hit at about 13:45 UTC ("try again at 6:19 PM"), roughly twenty minutes after the first live pipeline call (~13:25 UTC). The three builds had just finished; then **every S6 review on GitHub failed** (3 pipeline, 5 seeded PRs), as did the restarted #4 and #5 runs at S1. The re-ask fired 3 s later, against an error naming a reset hours away.

The fail-safe held (nothing approved or merged), but the PRs reached the human *unreviewed* until batch 2, which ADR-013's reservation was meant to prevent: it guards against running out of *money* within a run, not *quota* across runs.

Starting again, we would (1) put a **global governor** in front of every agent call (one queue and concurrency limit across all runs and experiments, not only per issue); (2) give the **reviewer its own quota pool**, so builds cannot starve reviews, which also strengthens independence; (3) make retries **quota-aware**: read the reset time, re-queue the review and post "review deferred" on the PR; and (4) **schedule experiments** away from live runs.

# 6. Limitations and threats to validity

1. **Small samples, one run per item, ceiling effects.** 5 issues and 5 seeded PRs, one run per arm: one flipped verdict moves E1 by 20 points. All valid E1 arms scored 5/5 and both E2 arms 19/19, so our items were too easy to separate the designs, and single differences (SP3) may be noise.
2. **We did not follow one pre-registered rule.** E2's rule said to supersede ADR-001; we kept it (§3.3).
3. **Different models across experiments and pipeline.** E2 and the local reviews of real changes used Gemini; E1's arms differ in harness; local E1 used the batch-1 models and GitHub the batch-2 models, so the GitHub 5/5 is not a same-model replication. E2's inputs for issues 4–5 came from local runs.
4. **No send-back on a real run.** The only real request for changes (PR #14) came from review-only mode, so the rework loop is tested only offline.
5. **We wrote the seeded PRs, hidden tests, reference fixes** and the vague issue's maintainer answer; the `bool` case (§3.2) shows our reference also makes interpretive choices.
6. **The fails-on-base check is weak** for features that add a new symbol (#3 and #4 fail on base with `ImportError`/`TypeError` whatever they assert) and at the level of individual tests (only one must fail; §4.3).
7. **Security and cost.** Orchestrator checks run agent-written code outside the sandbox, with network, while the ChatGPT `auth.json` (no spending cap) is readable; mitigated by write-access-only triggers, no fork PRs, deleting the file after the step, and revocation. Dollar figures are notional; only tokens are measured.

# Appendix A. Token and notional-cost totals

From `results/tokens.md` (generated by `experiment/scripts/tokens.py` over every saved ledger), grouped by role. "Input" is uncached input. Neither CLI reports cache writes, so there is no cache-write column.

| Role | Model | Kind | Calls | Input | Output | Cached input | Notional $ |
|---|---|---|---|---|---|---|---|
| Analyst | gpt-6.1-sol | GitHub + local | 11 | 342,511 | 33,155 | 661,376 | 1.52 |
| Analyst | gemini-3.8-flash-high | local | 3 | 264,647 | 240,490 | 1,721,434 | 0.94 |
| Judge | gpt-6.1-sol / gpt-6-luna / gemini (low) | GitHub + local | 7 | 108,687 | 1,739 | 12,416 | 0.20 |
| Architect | gpt-6.1-sol / gemini | GitHub + local | 6 | 306,227 | 109,722 | 1,547,799 | 1.03 |
| Developer | gpt-6.1-sol / gemini | GitHub + local + E2 | 11 | 576,363 | 147,147 | 3,703,827 | 1.37 |
| Tester | gpt-6.1-sol / gemini | GitHub + local + E2 | 11 | 568,648 | 185,244 | 3,134,229 | 1.44 |
| Builder (E2 B) | gemini-3.8-flash-high | E2 | 5 | 364,982 | 147,837 | 2,511,135 | 0.75 |
| Reviewer | gpt-6-astra | E1 | 5 | 183,827 | 21,572 | 623,616 | 0.94 |
| Friendly reviewer | gpt-6.1-sol | E1 | 5 | 174,657 | 20,051 | 677,120 | 0.91 |
| Reviewer | claude-opus-4-6-thinking | E1 | 5 | 230,921 | 34,664 | 1,164,074 | 2.60 |
| Reviewer | gemini-3.8-flash-high | E1 + real changes | 10 | 980,542 | 513,381 | 10,966,197 | 2.58 |
| Verifier | gpt-6-astra / gemini | E1 | 18 | 355,246 | 64,754 | 480,804 | 0.88 |
| Analyst | gpt-6.1-terra | GitHub (batch 2) | 5 | 135,964 | 12,532 | 180,864 | 0.29 |
| Judge, Architect, Developer, Tester | gpt-6.1-terra | GitHub (batch 2) | 8 | 165,520 | 8,094 | 448,640 | 0.32 |
| Reviewer | gpt-6-luna | GitHub (batch 2; real + seeded) | 10 | 319,342 | 49,664 | 1,492,992 | 0.58 |
| Verifier | gpt-6-luna | GitHub (batch 2) | 6 | 132,548 | 1,394 | 172,928 | 0.12 |
| **Total** | | | **126** | **5,210,632** | **1,591,440** | **29,499,451** | **16.46** |

Provider console: none, because subscriptions report no per-token bill. Hard spending limit: a subscription has none; its usage limit is the bound (ADR-014).

# Appendix B. Run links

Full list with notes: `results/runs.md`; one row per run: `results/results.csv`.

| Item | Actions run | PR | Final state |
|----------|------------|---|--------|
| Canary (Codex sandbox) | [45405561615](https://github.com/vishesh312/tinydb/actions/runs/45405561615) | — | success |
| Issue 1, batch 1 | [45405751306](https://github.com/vishesh312/tinydb/actions/runs/45405751306) | [#14](https://github.com/vishesh312/tinydb/pull/14) | awaiting-human (review invalid, quota) |
| Issue 2, batch 1 | [45405756174](https://github.com/vishesh312/tinydb/actions/runs/45405756174) | [#15](https://github.com/vishesh312/tinydb/pull/15) | awaiting-human (review invalid, quota) |
| Issue 3, batch 1 | [45405761409](https://github.com/vishesh312/tinydb/actions/runs/45405761409) | [#16](https://github.com/vishesh312/tinydb/pull/16) | awaiting-human (review invalid, quota) |
| Issue 4 runs 1 / 2, batch 1 | [45405768918](https://github.com/vishesh312/tinydb/actions/runs/45405768918) / [45406562390](https://github.com/vishesh312/tinydb/actions/runs/45406562390) | — | failed S1 (adapter bug) / failed S1 (quota) |
| Issue 5 runs 1 / 2, batch 1 | [45405774086](https://github.com/vishesh312/tinydb/actions/runs/45405774086) / [45406510262](https://github.com/vishesh312/tinydb/actions/runs/45406510262) | — | failed S1 (adapter bug) / failed S1 (quota) |
| Issues 1–3 review-only, batch 2 | [45430941471](https://github.com/vishesh312/tinydb/actions/runs/45430941471), [45430952227](https://github.com/vishesh312/tinydb/actions/runs/45430952227), [45430956918](https://github.com/vishesh312/tinydb/actions/runs/45430956918) | [#14](https://github.com/vishesh312/tinydb/pull/14)–[#16](https://github.com/vishesh312/tinydb/pull/16) | #14 changes requested; #15, #16 approved |
| Issue 4 run 3 / run 4 (after answer), batch 2 | [45431058108](https://github.com/vishesh312/tinydb/actions/runs/45431058108) / [45431998503](https://github.com/vishesh312/tinydb/actions/runs/45431998503) | [#20](https://github.com/vishesh312/tinydb/pull/20) | needs-info / approved, awaiting-human |
| Issue 5 run 3 / run 4 (after answer), batch 2 | [45431061462](https://github.com/vishesh312/tinydb/actions/runs/45431061462) / [45432006950](https://github.com/vishesh312/tinydb/actions/runs/45432006950) | [#21](https://github.com/vishesh312/tinydb/pull/21) | needs-info / approved, awaiting-human |
| Schema-adapter fix applied to the fork | — | [#13](https://github.com/vishesh312/tinydb/pull/13) | — |
| Seeded SP1–SP5 review-only, batch 1 | [45406746710](https://github.com/vishesh312/tinydb/actions/runs/45406746710), [45406751208](https://github.com/vishesh312/tinydb/actions/runs/45406751208), [45406760196](https://github.com/vishesh312/tinydb/actions/runs/45406760196), [45406765289](https://github.com/vishesh312/tinydb/actions/runs/45406765289), [45406768058](https://github.com/vishesh312/tinydb/actions/runs/45406768058) | [#7](https://github.com/vishesh312/tinydb/pull/7)–[#11](https://github.com/vishesh312/tinydb/pull/11) | awaiting-human (invalid, quota) |
| Seeded SP1–SP5 review-only, batch 2 | [45431078635](https://github.com/vishesh312/tinydb/actions/runs/45431078635), [45431083536](https://github.com/vishesh312/tinydb/actions/runs/45431083536), [45431089851](https://github.com/vishesh312/tinydb/actions/runs/45431089851), [45431098142](https://github.com/vishesh312/tinydb/actions/runs/45431098142), [45431104568](https://github.com/vishesh312/tinydb/actions/runs/45431104568) | [#7](https://github.com/vishesh312/tinydb/pull/7)–[#11](https://github.com/vishesh312/tinydb/pull/11) | 5/5 correct (A, C, C, C, C) |
| E1 local (4 arms) | local: `results/e1/codex-agyopus-run/`, `results/e1/xvendor-gemini/` | — | see §3.1 |
| E2 local (10 runs) | local: `results/e2/issue-N-{split,single}/` | — | all tests passed |
| Local pipeline runs | local: `results/local/` (`issue-1-luna-judge`, `issue-1-codex`, `issue-4-agy`, `issue-5-agy`, `issue-5-noanswer-agy`) | — | see §4.1 |
| Local reviews of real changes | local: `results/real-pr-reviews/` | — | 5/5 approve |

# Appendix C. Prompts and schemas

All prompts are in `workflow/prompts/` (index: `workflow/prompts/README.md`). System prompts have no placeholders; task templates use `{{NAME}}`. Analyst: `analyst.*` plus `workflow/skills/requirements-spec/SKILL.md` (the A1 skill, verbatim). Judge: `judge.*`. Architect: `architect.*`. Developer: `developer.*`. Tester: `tester.*`. Reviewer: `reviewer.*`. Verifier: `verifier.*`. E1 friendly reviewer: `reviewer_friendly.*`. E2 Builder: `builder.*`. Output schemas: `workflow/autose/schemas/*.schema.json` (contracts in DESIGN §14).

# Appendix D. AI use

I used a coding agent (Claude Code) substantially in this assignment (the same statement is in `README.md`). This is how the work was divided.

- **Design decisions.** For each decision area (stage boundaries, checks, agent roles, models, reviewer independence, routing, budgets, security, harness), I asked the agent for options. It proposed several design options, each with its rationale and trade-offs. I compared them and chose the option that seemed most appropriate for this project. The ADRs record the options considered and why the chosen one won.
- **My own design work and review.** I worked on the design myself. I reviewed the design document (`architecture/DESIGN.md`, the views and the ADRs) and the requirements documents (the spec and design schemas, the stage checks, and the issue texts with their expected behaviour), and had them revised where they did not match what I wanted.
- **Claude Ship features.** Partway through, I proposed adopting ideas from Anthropic's Claude Ship. The agent then adapted them into the pipeline: the Find → Verify review pass, the important / pre_existing / nit severities, and maintainer review rules read only from the base branch (ADR-015). I also decided to run the agents on my existing Codex and Antigravity subscriptions instead of a paid API (ADR-014), and later to switch to smaller models to save quota.
- **What the agent produced.** Under my direction, the coding agent wrote the orchestrator code and its tests, the GitHub workflows, the agent prompts, the diagrams, the text of the ADRs, DESIGN.md, this README and the report, and the experiment material (issue texts, hidden tests, reference patches and seeded PRs). It also ran the local experiments and triggered the GitHub runs I asked for.
- **Review.** I reviewed the generated material. The coding agent was also used for a separate second-pass review of the code and documents, and the defects it found are recorded in the ADRs and `results/runs.md`.

All runs, PRs and results are real and linked from `results/runs.md`. Model usage by the workflow itself (Codex on a ChatGPT subscription, with Antigravity for some local runs; ADR-014) is reported separately in [`results/tokens.md`](results/tokens.md).