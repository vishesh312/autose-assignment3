# Test report: issue #2

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | builder | S3 build | pass | compileall, import and mypy passed |
| 2 | builder | S4 test check | pass | AC mapping complete; 5 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 234, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_2.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_2.py::test_ac1_different_paths_compare_unequal`<br>`tests/test_autose_issue_2.py::test_ac1_same_path_and_nested_compatibility` |
| AC-2 | `tests/test_autose_issue_2.py::test_ac2_search_work_after_home` |
| AC-3 | `tests/test_autose_issue_2.py::test_ac3_search_home_after_work` |
| AC-4 | `tests/test_autose_issue_2.py::test_ac4_count_work_after_home_search` |
| AC-5 | `tests/test_autose_issue_2.py::test_ac5_get_work_after_home_search` |

## Full suite

- Result: **pass**
- Counts: {"tests": 234, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 5 new test(s) fail on base
