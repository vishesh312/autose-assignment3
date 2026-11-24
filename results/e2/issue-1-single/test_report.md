# Test report: issue #1

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | builder | S3 build | pass | compileall, import and mypy passed |
| 2 | builder | S4 test check | pass | AC mapping complete; 6 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_1.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_1.py::test_ac1_update_single_string_id`<br>`tests/test_autose_issue_1.py::test_ac1_update_query_cache_invalidation` |
| AC-2 | `tests/test_autose_issue_1.py::test_ac2_remove_single_string_id`<br>`tests/test_autose_issue_1.py::test_ac2_remove_query_cache_invalidation` |
| AC-3 | `tests/test_autose_issue_1.py::test_ac3_update_mixed_string_and_int_targets` |
| AC-4 | `tests/test_autose_issue_1.py::test_ac4_remove_mixed_string_and_int_targets` |
| AC-5 | `tests/test_autose_issue_1.py::test_ac5_update_all_missing_targets` |
| AC-6 | `tests/test_autose_issue_1.py::test_ac6_remove_all_missing_targets` |

## Full suite

- Result: **pass**
- Counts: {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 6 new test(s) fail on base
