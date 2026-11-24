# Test report: issue #4

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 12 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_4.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_4.py::test_ac1_limit_returns_first_n_matching_documents`<br>`tests/test_autose_issue_4.py::test_ac1_limit_equals_total_matches`<br>`tests/test_autose_issue_4.py::test_ac1_limit_with_interleaved_matches` |
| AC-2 | `tests/test_autose_issue_4.py::test_ac2_limit_exceeding_total_matches`<br>`tests/test_autose_issue_4.py::test_ac2_limit_exceeding_on_empty_table` |
| AC-3 | `tests/test_autose_issue_4.py::test_ac3_limit_zero_returns_empty_list`<br>`tests/test_autose_issue_4.py::test_ac3_limit_zero_on_empty_table` |
| AC-4 | `tests/test_autose_issue_4.py::test_ac4_limit_none_and_omitted_returns_all_matches` |
| AC-5 | `tests/test_autose_issue_4.py::test_ac5_table_search_with_limit`<br>`tests/test_autose_issue_4.py::test_ac5_table_search_limit_multiple` |
| AC-6 | `tests/test_autose_issue_4.py::test_ac6_query_cache_isolation_across_different_limits`<br>`tests/test_autose_issue_4.py::test_ac6_query_cache_unlimited_first_then_limited` |

## Full suite

- Result: **pass**
- Counts: {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 12 new test(s) fail on base
