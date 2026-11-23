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
| | | | | | |

`item` is `<seeded PR id> / A` (independent) or `<seeded PR id> / B` (friendly). Real AutoSE PRs reviewed by variant B are listed here too.

## E2 local runs

| item | Actions run | PR | review | status | notes |
|---|---|---|---|---|---|
| | | | | | |

`item` is `issue-N / split` or `issue-N / single`. These run locally with `autose local` on frozen S1–S2 inputs, so `Actions run`, `PR` and `review` are `local (no GitHub)`, and `notes` names the saved ledger path (`results/e2/issue-N-<variant>/ledger.jsonl`).

## Canary runs

| item | Actions run | PR | review | status | notes |
|---|---|---|---|---|---|
| | | | | | |

Canaries (DESIGN §10.1, ADR-011): `--bare` ignores a planted `CLAUDE.md` and hook, a denied tool is really denied, `structured_output` comes back in the expected shape, and the bash sandbox setting works on `ubuntu-latest`.
