# Token and cost accounting

The brief asks for the total number of tokens used. This file sums them.

**Sources.**
- Primary: `ledger.jsonl` from every run, one line per agent call, with fields `tokens_in`, `tokens_out`, `cache_read`, `cache_write`, `cost_usd`, `model`, `actor` (role), `run_id` (DESIGN §14). Workflow artifacts expire after 90 days, so each run's ledger is copied to `results/ledgers/<run-id>.jsonl` as soon as the run ends (ADR-004).
- Cross-check: the Anthropic provider console (usage and cost for the dedicated API key over the same period). Any gap between the ledger total and the console total is reported here, not hidden. Calls outside the ledger (canaries, local debugging, failed CLI starts) show up only in the console.
- Cache writes: `cache_write` is the CLI's `cache_creation_input_tokens`; ADR-006 expects cache writes to be a large part of cost, so they are summed separately.

## Per role (all runs)

| Role | Model | Calls | tokens_in | tokens_out | cache_read | cache_write | cost_usd |
|---|---|---|---|---|---|---|---|
| Analyst | claude-sonnet-5-5 | | | | | | |
| Judge | claude-haiku-5-5 | | | | | | |
| Architect | claude-sonnet-5-5 | | | | | | |
| Developer | claude-sonnet-5-5 | | | | | | |
| Tester | claude-sonnet-5-5 | | | | | | |
| Reviewer (A, independent) | claude-opus-5-5 | | | | | | |
| Reviewer (B, friendly, E1) | claude-sonnet-5-5 | | | | | | |
| Builder (E2 single) | claude-sonnet-5-5 | | | | | | |
| Canaries | claude-haiku-5-5 | | | | | | |
| **Total** | | | | | | | |

## Per run

One row per run listed in `runs.md` (same `item` names).

| Run (item) | Kind (pipeline / E1 / E2 / canary) | Run link or ledger path | Calls | tokens_in | tokens_out | cache_read | cache_write | cost_usd |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## Total

| Source | tokens_in | tokens_out | cache_read | cache_write | Total tokens | cost_usd |
|---|---|---|---|---|---|---|
| Sum of `ledger.jsonl` | | | | | | |
| Provider console | | | | | | |
| Difference (and why) | | | | | | |

Provider hard spend limit set on the key: $____ (date set: ____).
