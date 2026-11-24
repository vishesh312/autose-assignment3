# Runs

Every link in this file must be real and must open: an Actions run URL, PR URL or review URL on `vishesh312/tinydb` (kept public until grades are released). The brief's honesty rule applies: all runs, PRs and results must be real and linkable, and a fabricated run receives zero marks. A row is added only after the run exists; failed, stopped and aborted runs are recorded too, never deleted. Local runs with no GitHub URL say so explicitly and link to their saved `ledger.jsonl` under `results/` instead.

In `notes`, record for every run: the submission-repo commit it used (`sub@<sha>`, ADR-012), the start and end time in UTC (ADR-010 uses these to detect overlapping runs), the stop reason if it stopped, and the run's cost from `ledger.jsonl`. Per-run metrics go into `results.csv`; tokens and cost are summed in `tokens.md`.

## Pipeline runs (5 issues)

| item | Actions run | PR | review | status | notes |
|---|---|---|---|---|---|
| issue-1 | | | | | |
| issue-2 | | | | | |
| issue-3 | | | | | |
| issue-4 | | | | | |
| issue-5 (before answer) | | | | | |
| issue-5 (after answer, re-trigger) | | | | | |

## Seeded-PR review runs (E1)

| item | Actions run | PR | review | status | notes |
|---|---|---|---|---|---|
| SP1 (seeded) | not run yet | [#7](https://github.com/vishesh312/tinydb/pull/7) | — | PR open | opened by `open_seeded_prs.sh`; review is triggered with `/autose review` |
| SP2 (seeded) | not run yet | [#8](https://github.com/vishesh312/tinydb/pull/8) | — | PR open | opened by `open_seeded_prs.sh`; review is triggered with `/autose review` |
| SP3 (seeded) | not run yet | [#9](https://github.com/vishesh312/tinydb/pull/9) | — | PR open | opened by `open_seeded_prs.sh`; review is triggered with `/autose review` |
| SP4 (seeded) | not run yet | [#10](https://github.com/vishesh312/tinydb/pull/10) | — | PR open | opened by `open_seeded_prs.sh`; review is triggered with `/autose review` |
| SP5 (seeded) | not run yet | [#11](https://github.com/vishesh312/tinydb/pull/11) | — | PR open | opened by `open_seeded_prs.sh`; review is triggered with `/autose review` |

`item` is `<seeded PR id> / A` (independent) or `<seeded PR id> / B` (friendly). Real AutoSE PRs reviewed by variant B are listed here too.

## E2 local runs

| item | Actions run | PR | review | status | notes |
|---|---|---|---|---|---|
| | | | | | |

`item` is `issue-N / split` or `issue-N / single`. These run locally with `autose local` on frozen S1–S2 inputs, so `Actions run`, `PR` and `review` are `local (no GitHub)`, and `notes` names the saved ledger path (`results/e2/issue-N-<variant>/ledger.jsonl`).

## Canary runs

| item | Actions run | PR | review | status | notes |
|---|---|---|---|---|---|
| fork setup: `ci.yml` on push to `main` (no LLM) | [45340122654](https://github.com/vishesh312/tinydb/actions/runs/45340122654) | — | — | success | First live run after syncing the workflow into the fork (fork `main` = `edff96a` + `92ea08a` ARCHITECTURE.md + `6a76a2a` AutoSE). Confirms the lean CI (pytest + mypy) works and that upstream's CI and publish workflows are gone. |
| claude CLI canary (`workflow_dispatch` → `canary`) | | | | not run yet | needs the `ANTHROPIC_API_KEY` secret |

Canaries (DESIGN §10.1, ADR-011): `--bare` ignores a planted `CLAUDE.md` and hook, a denied tool is really denied, `structured_output` comes back in the expected shape, and the bash sandbox setting works on `ubuntu-latest`.
