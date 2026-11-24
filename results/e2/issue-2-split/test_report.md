# Test report: issue #2

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 6 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_2.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_2.py::test_ac1_query_equality_different_paths`<br>`tests/test_autose_issue_2.py::test_ac1_query_equality_same_path`<br>`tests/test_autose_issue_2.py::test_ac1_query_equality_nested_and_root_paths` |
| AC-2 | `tests/test_autose_issue_2.py::test_ac2_search_work_after_home`<br>`tests/test_autose_issue_2.py::test_ac2_search_nested_path` |
| AC-3 | `tests/test_autose_issue_2.py::test_ac3_search_home_after_work` |
| AC-4 | `tests/test_autose_issue_2.py::test_ac4_count_work_after_home` |
| AC-5 | `tests/test_autose_issue_2.py::test_ac5_get_work_after_home` |

## Full suite

- Result: **pass**
- Counts: {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 6 new test(s) fail on base
