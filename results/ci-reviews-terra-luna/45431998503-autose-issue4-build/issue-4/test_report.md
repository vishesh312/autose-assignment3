# Test report: issue #4

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 8 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_4.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_4.py::test_ac1_limit_returns_first_matching_documents`<br>`tests/test_autose_issue_4.py::test_ac1_limit_can_be_passed_positionally` |
| AC-2 | `tests/test_autose_issue_4.py::test_ac2_named_table_limit_exceeds_matches` |
| AC-3 | `tests/test_autose_issue_4.py::test_ac3_explicit_none_returns_all_matches` |
| AC-4 | `tests/test_autose_issue_4.py::test_ac4_zero_limit_returns_empty_list` |
| AC-5 | `tests/test_autose_issue_4.py::test_ac5_negative_limit_raises_value_error` |
| AC-6 | `tests/test_autose_issue_4.py::test_ac6_limited_search_does_not_truncate_cached_results` |
| AC-7 | `tests/test_autose_issue_4.py::test_ac7_limit_applies_to_cached_unlimited_search` |

## Full suite

- Result: **pass**
- Counts: {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 8 new test(s) fail on base
