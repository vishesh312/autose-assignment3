# Test report: issue #4

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 11 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 239, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_4.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_4.py::test_ac1_limit_returns_first_matching_docs_in_order`<br>`tests/test_autose_issue_4.py::test_ac1_limit_interspersed_matches` |
| AC-2 | `tests/test_autose_issue_4.py::test_ac2_limit_exceeding_total_matches`<br>`tests/test_autose_issue_4.py::test_ac2_limit_equal_total_matches` |
| AC-3 | `tests/test_autose_issue_4.py::test_ac3_limit_zero_returns_empty_list`<br>`tests/test_autose_issue_4.py::test_ac3_limit_zero_on_empty_table` |
| AC-4 | `tests/test_autose_issue_4.py::test_ac4_limit_none_and_omitted_return_all_matches` |
| AC-5 | `tests/test_autose_issue_4.py::test_ac5_named_table_search_with_limit` |
| AC-6 | `tests/test_autose_issue_4.py::test_ac6_query_cache_isolation_and_no_leakage`<br>`tests/test_autose_issue_4.py::test_ac6_cache_unlimited_then_limited_then_unlimited`<br>`tests/test_autose_issue_4.py::test_ac6_returned_lists_are_fresh_copies` |

## Full suite

- Result: **pass**
- Counts: {"tests": 239, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 11 new test(s) fail on base
