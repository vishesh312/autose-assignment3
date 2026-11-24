# Test report: issue #4

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | builder | S3 build | pass | compileall, import and mypy passed |
| 2 | builder | S4 test check | pass | AC mapping complete; 8 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_4.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_4.py::test_ac1_limit_returns_first_n_matches` |
| AC-2 | `tests/test_autose_issue_4.py::test_ac2_limit_exceeding_total_matches` |
| AC-3 | `tests/test_autose_issue_4.py::test_ac3_limit_zero_returns_empty_list` |
| AC-4 | `tests/test_autose_issue_4.py::test_ac4_limit_none_preserves_default_behavior` |
| AC-5 | `tests/test_autose_issue_4.py::test_ac5_non_default_table_limit` |
| AC-6 | `tests/test_autose_issue_4.py::test_ac6_query_cache_isolation`<br>`tests/test_autose_issue_4.py::test_ac6_cache_isolation_unlimited_then_limited`<br>`tests/test_autose_issue_4.py::test_ac6_result_list_mutation_isolation` |

## Full suite

- Result: **pass**
- Counts: {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 8 new test(s) fail on base
