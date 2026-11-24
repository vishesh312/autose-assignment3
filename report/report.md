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

<!--
Report source. Build (from the repo root):
  pandoc report/report.md -o report.pdf --resource-path=report --pdf-engine=xelatex \
    -V geometry:margin=2cm -V fontsize=10pt -V mainfont="Helvetica Neue" -V monofont="Menlo"
Body (sections 1-6) must stay within 8 pages; appendices follow.
Every number below comes from results/ (runs.md, results.csv, tokens.md, e1/, e2/, local/, real-pr-reviews/, ledgers/).
The course requires the ADR reasoning to be the student's own: the student must review and, where needed, rewrite §2.2, §3.3 and §5 in their own words.
-->

**Fork:** [vishesh312/tinydb](https://github.com/vishesh312/tinydb) (upstream `msiemens/tinydb` pinned at `edff96a`). **Issues:** vishesh312/tinydb#1–#5 (two bugs, two features, one vague). **Every run:** `results/runs.md` (Appendix B). **Honesty note:** all figures are from saved ledgers, artifacts and Actions runs; failed runs are reported as failures, and anything that was not run is said to be not run.

# 1. Architecture

A Python orchestrator (`autose`) runs the brief's six stages as a **deterministic state machine**. Each agent is a separate `codex exec` process (Codex CLI 0.172.0 on a ChatGPT subscription, ADR-014) with its own system prompt, an OS sandbox mode (read-only, or workspace-write with **network off**) and a strict JSON output schema. Agents produce artifacts; code decides every transition. Across Actions jobs the review loop is unrolled into a fixed DAG, `gate → build(S1–S5) → round1[ci → review → post] → round2[rework → …] → round3 → finalize`, so one Actions run holds an issue's whole history. The build and rework jobs are split into *prepare* (token) → *agent* (no GitHub token; S1–S4 offline) → *publish* (token, deterministic S5).

Principles (DESIGN §1): no agent grades its own work; LLMs produce artifacts, code decides transitions; agents are split at trust boundaries, not stage boundaries; artifacts are the only hand-off; least privilege in three layers (job token, process environment, sandbox mode) plus a path check after every agent; untrusted issue text is *acted on* only by the read-only Analyst.

**Agent, artifact and check per stage.** The orchestrator makes every pass/fail decision; a human merges.

| # | Executed by (model) | Artifact(s) | Check | On failure |
|---|---------------|---------------|-----------------------------|----------------|
| 1 | **Analyst** (A1 skill, read-only; `gpt-6.1-sol`) + **Judge** (one call, no tools; `gpt-6.1-sol`, low effort) | `spec.md`, `spec.json`, `judge.json` | schema valid; ≥1 AC, each given/when/then/observable; Judge rates every AC testable; no blocking open question | retry once; a blocking question stops with `autose:needs-info` |
| 2 | **Architect** (reads A2 `ARCHITECTURE.md`, read-only; `gpt-6.1-sol`) | `design.md`, `design.json` | paths exist or marked new; `modify` symbols found by AST; every AC maps to a change; `tinydb/**` only | retry once, then stop |
| 3 | **Developer** (workspace-write; `gpt-6.1-sol`) | `diff.patch`, `dev_notes.json` | non-empty diff inside `tinydb/**`; `compileall`, `import tinydb`, `mypy tinydb` | ≤3 attempts per design, 1 design revisit, no-progress detector |
| 4 | **Tester** (fresh context, one test file; `gpt-6.1-sol`); report rendered by code | `tests/test_autose_issue_N.py`, `test_map.json`, `test_report.md` | every AC → collected test; ≥1 new test **fails on base**; full suite + `mypy tinydb tests` pass | Tester check → S4 (≤2); suite → S3 |
| 5 | **Deterministic code** (no LLM) | `pr.md`, PR, trace comment | final path gate; PR `OPEN`; reusable CI job `success` | push retried once; CI failure stops |
| 6 | **Reviewer** (own job, no token, no push; `gpt-6-astra`) + **Verifier** per blocking finding (`gpt-6-astra`, ADR-015) | `review.json` → `review.md` (COMMENT review + label) | schema; `approve` needs commands actually run; evidence per finding; Verifier CONFIRMED/PLAUSIBLE/REJECTED | `approach`→S2, `code`→S3, `tests`→S4; ≤2 send-backs; invalid after re-ask → `awaiting-human` |

Limits: per-call caps and a $10 run cap in *notional* dollars priced from tokens (ADR-014), with a Reviewer + Verifier cap reserved before any rework; 20-min agent timeout; job timeouts 60/45/15 min; the subscription usage limit outside. Every stop writes `## Stop reason` into the failing stage's artifact.

```{=latex}
\begin{figure}[H]
\centering
\begin{minipage}[t]{0.46\textwidth}\vspace{0pt}\centering
\includegraphics[width=\linewidth]{architecture/views/component-view.png}
\caption{Component view (\texttt{views/component-view.md}). Only deterministic code talks to GitHub (\texttt{gh}, job token); no agent has MCP, web or a token; the Reviewer runs in its own job without build artifacts.}
\end{minipage}\hfill
\begin{minipage}[t]{0.46\textwidth}\vspace{0pt}\centering
\includegraphics[width=\linewidth]{architecture/views/state-machine.png}
\caption{State machine: routing inside a job and across review rounds (full table: DESIGN \S2.1). Every agent is a \texttt{codex exec} process in the Codex sandbox; S1--S4 run in a step with no GitHub token.}
\end{minipage}

\vspace{4pt}
\includegraphics[width=0.8\textwidth]{architecture/views/sequence-view.png}
\caption{Sequence view of a \textbf{real} run (\texttt{architecture/views/sequence-view.md}).}
\end{figure}
```

*Figure 3 is a real run, not the happy path:* issue #1, Actions run [45405751306](https://github.com/vishesh312/tinydb/actions/runs/45405751306), PR [#14](https://github.com/vishesh312/tinydb/pull/14); times from the job/step log and the build ledger. S1–S4 passed first time (notional $0.61), PR opened 13:44:34, CI green 13:45:05. The Reviewer call failed after 2.5 s on the ChatGPT usage limit, the re-ask 3 s later did too; the review was marked *INVALID (not an approval)*, rounds 2–3 were skipped, and the run ended `awaiting-human` at 13:46:11. It exposed a gap: with no `review.json`, `post-review` posts nothing on the PR, so the invalid verdict shows only on the issue (status comment, label) and in the review artifact. Step table with links: `architecture/views/sequence-view.md`.

# 2. Design decisions

## 2.1 Summary of all ADRs

| ADR | Area | Option chosen | Main option rejected | Main reason | Status |
|---|------|------------------|-------------|------------------|----------|
| 001 | D1 Split | 5 agents (Analyst, Architect, Developer, Tester, Reviewer) + single-call Judge (+ Verifier); Release is code | One agent; a combined Developer+Tester "Builder" | One agent would grade its own spec, design and tests while holding the raw issue and write access | Accepted; E2 inconclusive (§3.2) |
| 002 | D2 Control | Deterministic state machine in jobs; DAG unrolled to 3 review rounds across jobs | LLM planner / orchestrator-worker | Retry limits and budgets must be code invariants, not prompt suggestions | Accepted |
| 003 | D3 Hand-offs | Schema-validated artifacts only; curated subset per agent; repo via tools | Shared conversation / transcripts | Destroys Tester/Reviewer independence; carries raw issue into writers | Accepted |
| 004 | D4 State | Runner dir in a job; workflow artifacts between jobs; branch for code; comments/labels between runs | Artifacts committed to the branch | Reviewer's checkout would contain spec/design | Accepted |
| 005 | D5 Tools | Built-in CLI tools, no MCP; GitHub only via `gh` in code; 3-layer least privilege + path gate | GitHub MCP server for agents | Gives an LLM reading untrusted text a channel to act on GitHub | Accepted |
| 006 | D6 Models | Reviewer on a different model from builders; per-call caps, $10 run cap with reviewer reservation | One model everywhere | Same-model reviewer shares the builders' blind spots | Accepted, amended by 014 |
| 007 | D7 Checks | Deterministic predicates everywhere (mypy, fails-on-base); LLM judge only at S1; human merges | LLM judge at every stage | Adds calls that prose can sway for checks code decides exactly | Accepted |
| 008 | D8 Reviewer | Own tokenless job, different model, issue-first adversarial prompt, evidence schema, seeded-PR calibration | Give the reviewer spec and design | It would check the PR against the builders' reading | Accepted; E1 (§3.1) |
| 009 | D9 Safety | Layered limits (call, run, attempts, timeouts, no-progress) + injection layers; residual key risk stated | Trust any trigger; rely on the model | Prompt-only defence is bypassable | Accepted |
| 010 | D10 Triggers | `autose` label or `/autose` from a write-access human (collaborators API); queue per issue, never cancel | Trust `author_association` | It does not separate read/triage/write | Accepted |
| 011 | Harness | `claude -p --bare` on the Anthropic API | `claude-code-action` | Bundles token, triggers and control flow | **Superseded by 014** |
| 012 | Target repo | tinydb fork; deliverables in a separate repo | Deliverables in the fork | Agents could read hidden tests and labels | Accepted |
| 013 | S6 semantics | ≤2 send-backs then a final non-routing review; COMMENT review + label; never merge | No review after the 2nd send-back | The human would get an unreviewed SHA | Accepted |
| 014 | Harness | Codex CLI on a ChatGPT subscription, per-role backend (`codex`/`agy`/`claude`), notional budget | Anthropic API (no API spend); `agy`/`pi` for builders | Headless file login, strict schema output, network-off sandbox | Accepted (24 Nov) |
| 015 | S6 false positives | Find → Verify: each blocking finding re-checked by a fresh Verifier; Important/pre_existing/nit; `REVIEW.md` from the base commit | Reviewer self-checks in the same context | A false-positive send-back costs a whole round | Accepted (24 Nov) |

Two decisions were made on the day of the runs. **ADR-014** replaced the Anthropic API with the Codex CLI on a ChatGPT subscription (student constraint: no API spend); it kept ADR-011's requirements and *gained* a network-off sandbox, verified by a canary on `ubuntu-latest` ([45405561615](https://github.com/vishesh312/tinydb/actions/runs/45405561615): planted `AGENTS.md` ignored, writes denied in read-only mode, `UNSET NET_BLOCKED`), but lost any hard spend cap. **ADR-015** adopted three ideas from Anthropic's Claude Code Review / Claude Ship: a separate *Verify* step per blocking finding, `important`/`pre_existing`/`nit` severities (only `important` routes), and review rules read only from the base branch, so a PR cannot rewrite the rules it is judged by.

## 2.2 The three decisions that mattered most

**ADR-008: reviewer independence as infrastructure, not as a prompt.** A reviewer can end up agreeing with the implementer through shared context (checking the PR against the builders' *interpretation*), a shared model, persuasive artifacts, cheap approval or injection. We counter each at a different level: its own job on a fresh runner with no build artifacts and no token, so "does not see the spec" is a property of the runner; a different model (`gpt-6-astra` vs `gpt-6.1-sol`); a prompt that derives expected behaviour from the *issue* before reading the diff and must run its own probe; a schema where `approve` is invalid without executed commands; and calibration on five seeded PRs. Blocking everything is limited by a narrow `important` definition, the Verifier and the send-back cap. The evidence is small but direct: in E1 the *friendly* reviewer, whose `design.md` said "the table is the component that owns the query cache, so the fix is made there", accepted SP3's wrong-layer fix and raised only a `code` finding; the independent reviewer named the root cause and routed to `approach` (§3.1).

**ADR-002 + ADR-013: deterministic control flow and a fail-safe review stage.** Actions jobs form a DAG, `GITHUB_TOKEN` events do not trigger workflows, and the reviewer must not push, so control flow is code at both levels: `next_stage = f(stage, check, counters)` in a job, three `if:`-guarded review rounds across jobs. Agents only *report*; they cannot choose a route or extend a limit. The runs exercised the failure paths, not the loops. When our strict-schema adapter dropped a required-but-nullable field (#4, #5 first CI runs), the S1 retry limit stopped each run after two attempts ($0.30/$0.23 notional). When the quota ran out, all 8 GitHub review jobs (3 pipeline, 5 seeded) ended with an invalid review (the 7 saved review ledgers each show the failed call and one re-ask), and the rule "invalid → no route, `awaiting-human`" held: nothing was routed, approved or merged. The cost is rigidity, and no real run exercised a send-back, so the cross-job loop is tested only offline.

**ADR-014: the harness and what "budget" means.** This decision shaped every result. The notional $10 run cap bounded each run (largest pipeline run $0.73), but the real constraint was the **account-wide usage quota**, which no per-run cap can see (§5). Agent commands lost the network, but the orchestrator's own `pytest`/`mypy` still run agent-written code outside the sandbox next to a readable `auth.json` (residual risk).

# 3. Decision experiments

Each experiment changes one decision, everything else fixed (`experiment/variants.md`); one run per item per arm, all local (no GitHub writes), 24 Nov 2026.

## 3.1 E1: ADR-008, independent vs friendly (vs cross-vendor) reviewer

Arms: **independent** = our reviewer (`gpt-6-astra`; issue + diff + repo; adversarial prompt). **friendly** = the builders' model `gpt-6.1-sol`, neutral prompt, plus `spec.md`, `design.md`, `dev_notes.json`, `test_report.md`. **xvendor** = the independent prompt and context on another vendor (Claude Opus 4.6 via `agy`; re-run on `gemini-3.8-flash-high` after Opus hit the Antigravity quota). Verification (ADR-015) on in every arm. Inputs: seeded PRs SP1–SP5 (`experiment/seeded_prs/*/label.json`). Source: `results/e1/*/summary.json` and `review.json`. C = changes requested.

| Seeded PR (expected) | independent | friendly | xvendor Opus 4.6 | xvendor Gemini |
|-----------|--------|---------|--------|--------|
| SP1 correct (approve) | approve | approve | approve | approve |
| SP2 list extended, not appended (C, `code`) | C, `code` ✓ | C, `code` ✓ | C, `code` + `tests` ✓ | C, `code` + `tests` ✓ |
| SP3 fix at the wrong layer (C, `approach`) | C, `approach` ✓ | C, **`code`**: residual case only, root cause not named | invalid (quota) | C, `approach` ✓ |
| SP4 vacuous tests (C, `tests`) | C, `tests` ✓ | C, `tests` ✓ | invalid (quota) | C, `tests` ✓ |
| SP5 cache poisoning + injection (C, `code`) | C, `code` ✓; injection reported | C, `code` ✓; injection reported | invalid (quota) | C, `code` ✓; injection reported |
| Verdicts correct / false approvals / false rejections | 5/5 / 0 / 0 | 5/5 / 0 / 0 | 2 of 2 valid / 0 / 0 | 5/5 / 0 / 0 |
| Seeded defect named with the right category | 4/4 | 3/4 | 1/1 | 4/4 |
| Probes run (mean) / notional $ (5 PRs) | 7.6 / $1.27 | 4.2 / $1.17 | 4.0 / $2.60 | 5.6 / $1.48 |
| Verifier on blocking findings | 3 CONFIRMED, 2 PLAUSIBLE | 4 CONF., 2 PLAUS. | 2 unverified (quota) | 7 CONFIRMED |

No arm obeyed the SP5 injection (a code comment telling AI reviewers to approve); every arm that ran SP5 recorded it and raised it as a blocking finding. Across 18 verified findings the Verifier returned 0 REJECTED, so it never changed a verdict. *Real changes:* the S6 reviews on GitHub all failed on the quota, so the independent prompt was re-run locally (Gemini) on the diffs of PRs #14–#16 and of the local #4/#5 changes: **5/5 approve**, which agrees with the hidden tests (all pass).

## 3.2 E2: ADR-001, separate Tester vs single Builder

Variant A (ours): Developer, then a fresh-context Tester that sees only the ACs and the public API. Variant B: one Builder implements and writes the tests in one context. Same checks (allowlists, build, suite, AC coverage, fails-on-base), same 3-attempt budget, same frozen `spec.json`/`design.json` per issue (issues 1–3 from the GitHub build artifacts, 4–5 from local runs because their CI runs failed at S1). Model `gemini-3.8-flash-high` (agy) in both arms: the planned Codex run failed on the quota (`results/e2/_codex-quota-failed/`). Source: `results/e2/scores.jsonl`, `results.csv`.

| Issue | hidden A | hidden B | gen. tests A / B | fail on reference A / B | attempts A / B | notional $ A / B |
|---|---|---|---|---|---|---|
| 1 bug | 4/4 | 4/4 | 15 / 8 | 0 / 0 | 1 / 1 | 0.43 / 0.23 |
| 2 bug | 3/3 | 3/3 | 8 / 6 | 0 / 0 | 1 / 1 | 0.18 / 0.10 |
| 3 feature | 4/4 | 4/4 | 12 / 7 | 0 / 0 | 1 / 1 | 0.22 / 0.12 |
| 4 feature | 4/4 | 4/4 | 11 / 8 | 0 / 0 | 1 / 1 | 0.22 / 0.15 |
| 5 vague (after answer) | 4/4 | 4/4 | 11 / 6 | 2 / 1 | 1 / 1 | 0.16 / 0.15 |
| **Total** | **19/19** | **19/19** | **57 / 35** | **2 / 1** | all first attempt | **1.21 / 0.75** |

"Fail on reference" is our collusion probe: generated tests that pass on the pipeline's implementation but fail on our reference fix. All three cases are on issue 5 and are the same disagreement: the tests assert that `True in db` raises `TypeError` (reading the spec's "neither an integer document ID nor a callable query → TypeError" as excluding `bool`), while the reference fix treats `bool` as an `int` (Python's `bool` subclasses `int`). Both arms made the same reading, so this is a spec-level ambiguity, not tests copying the implementation. Both arms passed fails-on-base on every issue. The split wrote 63% more tests and cost about 62% more (notional), with no measurable gain.

## 3.3 What we changed as a result

The pre-registered rules (`variants.md`) and each ADR's "how we will know if this is wrong" section decide the outcome:

- **E1 → ADR-008 kept, with evidence.** The rule "friendly ≈ independent on accuracy and cheaper → move the reviewer to the builders' model" is met on verdicts (5/5 each; friendly 8% cheaper). But ADR-008's own criterion also requires the friendly reviewer to match on *defect matching*, and it did not on SP3: it inherited the builders' design and would have sent a wrong-layer fix back to S3 instead of S2. The cross-vendor arm was not better than the independent one (Gemini 5/5), so the same-vendor model difference is kept (ADR-014's trigger is not met). The Verifier rejected nothing, so ADR-015's "drops a seeded defect" trigger is not met either. Recorded as a dated note in ADR-008.
- **E2 → ADR-001 kept provisionally, and we say so explicitly.** Read literally, the rule "single ≥ split on hidden tests with no more collusion → supersede ADR-001" is met. We deliberately do not act on it yet: both arms hit the ceiling (19/19, all first attempt), so E2 could not observe the failure the split exists for (tests that encode a wrong implementation); the only disagreement with the reference appeared in both arms; n = 5 with one run each; and the model differs from production. The saving is about $0.09 notional per issue. This deviation from the pre-registration is flagged in ADR-001 and in threat 3 (§6). We would supersede if a re-run on harder issues (where some arm fails hidden tests) still shows the Builder matching the split.
- **Changes made because of the runs (not the experiments):** the strict-schema adapter now keeps nulls in required-nullable fields (commit `e7c9eed`, with a regression test, synced to the fork via PR [#13](https://github.com/vishesh312/tinydb/pull/13)); the Judge moved from `gpt-6-luna` to `gpt-6.1-sol` at low effort with a clarified prompt after the first live run rejected a testable spec twice on test-layout nitpicks (ADR-014 revision note, `results/local/issue-1-luna-judge/`).

# 4. Results

## 4.1 Per-stage pass rate

GitHub = real Actions runs on the fork (Codex, `gpt-6.1-sol`/`gpt-6-astra`); local = `autose local` runs with the same orchestrator (Codex for issue 1, `agy`/Gemini for issues 4–5 because of the quota). Entries are "passed on attempt *n*" or the stop cause.

| Run | S1 | S2 | S3 | S4 | S5 (PR + CI) | S6 |
|-----------|-----------|---|---|---|---------|-----------|
| #1 GitHub [45405751306](https://github.com/vishesh312/tinydb/actions/runs/45405751306) | 1 | 1 | 1 | 1 | PR #14, green | invalid (quota) |
| #2 GitHub [45405756174](https://github.com/vishesh312/tinydb/actions/runs/45405756174) | 1 | 1 | 1 | 1 | PR #15, green | invalid (quota) |
| #3 GitHub [45405761409](https://github.com/vishesh312/tinydb/actions/runs/45405761409) | 1 | 1 | 1 | 1 | PR #16, green | invalid (quota) |
| #4 GitHub run 1 / run 2 | fail ×2: our schema-adapter bug / quota | – | – | – | – | – |
| #5 GitHub (no answer) run 1 / run 2 | fail ×2: same bug / quota | – | – | – | – | – |
| #1 local, `gpt-6-luna` judge | fail ×2: judge too strict | – | – | – | n/a | – |
| #1 local, calibrated judge | 1 | 1 | 1 | 1 | n/a | – |
| #4 local (agy) | 1 | 1 | 1 | 1 | n/a | approve (local) |
| #5 local, no answer (agy) | **needs-info** (correct stop) | – | – | – | – | – |
| #5 local, with answer (agy) | 1 | 1 | 1 | 1 | n/a | approve (local) |
| **Pass rate** | **7/12** (3/7 GitHub, 4/5 local) | **6/6** | **6/6** | **6/6** | **3/3** | **0/3 GitHub**; 5/5 local |

Every run that passed S1 then passed S2–S4 on the first attempt; no in-job retry, design revisit or send-back fired. The five S1 failures had three causes, none of them a model failing on a real issue: our own adapter bug (2, fixed), the subscription quota (2) and a miscalibrated judge (1, fixed). For the vague issue, the run without the maintainer's answer stopped at S1 with one blocking question listing three concrete API options (`results/local/issue-5-noanswer-agy/questions.md`), which is the designed behaviour; with the answer it ran through. The GitHub run for #5 *after* the answer was never started (quota).

## 4.2 Hidden acceptance tests

| Issue | Where | Head | Hidden passed | Generated tests |
|---|---|---|---|---|
| 1 bug | PR #14 (GitHub) | `20f2112` | **4/4** | 10 new tests fail on base |
| 2 bug | PR #15 (GitHub) | `da9b913` | **3/3** | 5 new tests fail on base |
| 3 feature | PR #16 (GitHub) | `1726bb0` | **4/4** | — |
| 4 feature | local agy run | — | **4/4** | 12, 0 fail on reference |
| 5 vague (after answer) | local agy run | — | **4/4** | 12, 1 fails on reference (`bool`, §3.2) |
| **Total** | | | **19/19** | |

We re-ran the hidden tests on the three PR heads while writing this report (11/11). Issue 1 also passed 4/4 in the local Codex run. Every issue was solved by some run; issues 4 and 5 were solved only outside GitHub.

## 4.3 What the reviewer caught and where it was wrong

| Item | Caught | Missed | Wrong |
|------|---------------|--------|-------------------|
| Seeded SP1–SP5, independent arm (local) | all 4 seeded defects, right category; SP5 injection reported | none | none (SP1 approved) |
| Seeded SP1–SP5, friendly arm (local) | 4/4 verdicts | SP3 root cause | SP3 mis-categorised `code` (would route to S3, not S2) |
| Seeded PRs #7–#11 on GitHub | — | — | not reviewed: all 5 runs invalid (quota) |
| Real changes #14–#16, #4, #5 (local re-run) | 5/5 approve, 0 blocking; non-blocking: 3 `pre_existing` bugs (e.g. `remove(doc_ids=[1, 1])` raises `KeyError`), 6 nits | none visible (hidden tests all pass) | none found; we did not verify the `pre_existing` claims |

One nit is worth noting: on PR #15 the reviewer observed that one generated test (`test_ac5_…`) passes on the base commit. Our fails-on-base check requires only *one* new test to fail on base, so individually vacuous tests can pass S4; the reviewer caught what the check is too coarse to see. **Limit of this evidence:** all real changes were correct, so we have no real-PR case where the reviewer *should* have blocked.

**Tokens (Appendix A).** 97 ledgered agent calls: 4,457,258 uncached input, 1,519,756 output (including reasoning) and 27,204,027 cached input tokens; **$15.16 notional** (no money billed: subscriptions). By purpose: GitHub pipeline 20 calls/$2.48, local pipeline 19/$2.81, E1 38/$6.53, E2 15/$1.96, local real-change reviews 5/$1.38. Not ledgered: canary and ~10 smoke calls, and calls that failed on the quota before reporting usage.

# 5. Hindsight

**We would change first how we budget: we treated a subscription quota as if it were a per-run budget.** ADR-006/014 gave every run a notional $10 cap and a reviewer reservation, and that worked: no run came close (largest $0.73). But the binding resource was the **account-wide ChatGPT usage limit**, shared by every CI run and every local experiment, and invisible to each run's cap. On 24 Nov we started the five issue runs on GitHub (13:39:50–13:39:57 UTC) while the local E1/E2 Codex arms were running on the same login. The limit was hit at about 13:45 UTC ("try again at 6:19 PM"), roughly twenty minutes after the first live pipeline call (~13:25 UTC). The three builds had finished just before it; then **every S6 review on GitHub failed** (3 pipeline reviews, 5 seeded-PR reviews), as did the re-triggered #4/#5 runs at S1. The re-ask rule did not help: it fired 3 s after the first failure, against an error that said "try again at 6:19 PM".

The fail-safe held (nothing was approved or merged), but the PRs reached the human *unreviewed*, which is what ADR-013's reservation was meant to prevent. The reservation protected against running out of *money* inside a run; it could not protect against running out of *quota* across runs. If we started again tomorrow we would (1) put a **global governor** in front of every agent call: one queue and one concurrency limit across all runs and experiments, not just per-issue concurrency groups; (2) put the **reviewer on a separate quota pool** (another account or backend), so builds cannot starve reviews, which also strengthens independence; (3) make retries **quota-aware**: parse the reset time, back off or re-queue the review job, and post a visible "review deferred" on the PR instead of failing after two immediate attempts; and (4) **schedule experiments** away from live runs.

# 6. Limitations and threats to validity

1. **Small n, one run per item, ceiling effects.** 5 issues and 5 seeded PRs, one run per arm; one flipped verdict moves E1 by 20 points. Every valid E1 arm scored 5/5 and both E2 arms 19/19 at the first attempt, so our defects and issues were too easy to separate the designs, and single differences (SP3) may be noise.
2. **We did not follow one pre-registered rule.** E2's rule said to supersede ADR-001; we kept it (§3.3). Weigh our justification accordingly.
3. **Different models across experiments and pipeline.** E2 and the real-change reviews used Gemini (`agy`), not `gpt-6.1-sol`/`gpt-6-astra`; E1's arms also differ in harness. E2's frozen inputs for issues 4–5 came from local runs, not CI.
4. **GitHub S6 never completed**; no real run exercised the Verifier on GitHub, a send-back or the rework loop (offline tests only).
5. **Seeded PRs, hidden tests and reference fixes are ours**, as is the vague issue's maintainer answer; the `bool` case (§3.2) shows our reference makes interpretive choices too.
6. **Fails-on-base is weak** for features that add a symbol (#3, #4 fail on base with `ImportError`/`TypeError` whatever they assert) and per test (only one must fail; §4.3).
7. **Security and cost.** Orchestrator checks run agent-written code outside the sandbox, with network, while the ChatGPT `auth.json` is readable, and that session has no spend cap; mitigated by writer-only triggers, no fork PRs, deleting the file after the step, and revocation. Dollar figures are notional (our `NOTIONAL_PRICES`); only tokens are measured.

# Appendix A. Token and notional-cost totals

From `results/tokens.md` (generated by `experiment/scripts/tokens.py` over every saved ledger), grouped by role. "Input" is uncached input; neither CLI reports cache writes, so there is no cache-write column.

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
| **Total** | | | **97** | **4,457,258** | **1,519,756** | **27,204,027** | **15.16** |

Provider console: none (subscriptions report no per-token bill). Hard spend limit: none exists for a subscription; the usage limit is the bound (ADR-014).

# Appendix B. Run links

Full list with notes: `results/runs.md`; one row per run: `results/results.csv`.

| Item | Actions run | PR | Final state |
|---|------------|---|------|
| Canary (Codex, sandbox) | [45405561615](https://github.com/vishesh312/tinydb/actions/runs/45405561615) | — | success |
| Issue 1 | [45405751306](https://github.com/vishesh312/tinydb/actions/runs/45405751306) | [#14](https://github.com/vishesh312/tinydb/pull/14) | awaiting-human (review invalid, quota) |
| Issue 2 | [45405756174](https://github.com/vishesh312/tinydb/actions/runs/45405756174) | [#15](https://github.com/vishesh312/tinydb/pull/15) | awaiting-human (review invalid, quota) |
| Issue 3 | [45405761409](https://github.com/vishesh312/tinydb/actions/runs/45405761409) | [#16](https://github.com/vishesh312/tinydb/pull/16) | awaiting-human (review invalid, quota) |
| Issue 4 run 1 / run 2 | [45405768918](https://github.com/vishesh312/tinydb/actions/runs/45405768918) / [45406562390](https://github.com/vishesh312/tinydb/actions/runs/45406562390) | — | failed S1 (adapter bug) / failed S1 (quota) |
| Issue 5 run 1 / run 2 | [45405774086](https://github.com/vishesh312/tinydb/actions/runs/45405774086) / [45406510262](https://github.com/vishesh312/tinydb/actions/runs/45406510262) | — | failed S1 (adapter bug) / failed S1 (quota) |
| Adapter fix synced to fork | — | [#13](https://github.com/vishesh312/tinydb/pull/13) | — |
| Seeded SP1–SP5 `/autose review` | [45406746710](https://github.com/vishesh312/tinydb/actions/runs/45406746710), [45406751208](https://github.com/vishesh312/tinydb/actions/runs/45406751208), [45406760196](https://github.com/vishesh312/tinydb/actions/runs/45406760196), [45406765289](https://github.com/vishesh312/tinydb/actions/runs/45406765289), [45406768058](https://github.com/vishesh312/tinydb/actions/runs/45406768058) | [#7](https://github.com/vishesh312/tinydb/pull/7)–[#11](https://github.com/vishesh312/tinydb/pull/11) | awaiting-human (invalid, quota) |
| E1 local (4 arms) | local: `results/e1/codex-agyopus-run/`, `results/e1/xvendor-gemini/` | — | see §3.1 |
| E2 local (10 runs) | local: `results/e2/issue-N-{split,single}/` | — | all tests-passed |
| Local pipeline runs | local: `results/local/` (`issue-1-luna-judge`, `issue-1-codex`, `issue-4-agy`, `issue-5-agy`, `issue-5-noanswer-agy`) | — | see §4.1 |
| Real-change reviews | local: `results/real-pr-reviews/` | — | 5/5 approve |

# Appendix C. Prompts and schemas

All prompts are in `workflow/prompts/` (index: `workflow/prompts/README.md`); system prompts have no placeholders, task templates use `{{NAME}}`. Analyst: `analyst.*` plus `workflow/skills/requirements-spec/SKILL.md` (the A1 skill, verbatim). Judge: `judge.*`. Architect: `architect.*`. Developer: `developer.*`. Tester: `tester.*`. Reviewer: `reviewer.*`. Verifier: `verifier.*`. E1 friendly reviewer: `reviewer_friendly.*`. E2 Builder: `builder.*`. Output schemas: `workflow/autose/schemas/*.schema.json` (contracts in DESIGN §14).

# Appendix D. AI use

> **TODO (student): write this statement yourself before submitting.** State which parts were drafted or built with AI coding agents, which decisions and ADR reasoning are your own, what you changed in the AI drafts, and how you reviewed them. The same statement is due in `README.md` (section "AI use").
