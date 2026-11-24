# Test report: issue #1

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 10 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_1.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_1.py::test_ac1_update_numeric_string_id[memory-default]`<br>`tests/test_autose_issue_1.py::test_ac1_update_numeric_string_id[memory-named]`<br>`tests/test_autose_issue_1.py::test_ac1_update_numeric_string_id[json-default]`<br>`tests/test_autose_issue_1.py::test_ac1_update_numeric_string_id[json-named]` |
| AC-2 | `tests/test_autose_issue_1.py::test_ac2_remove_numeric_string_id[memory-default]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_numeric_string_id[memory-named]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_numeric_string_id[json-default]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_numeric_string_id[json-named]` |
| AC-3 | `tests/test_autose_issue_1.py::test_ac3_update_mixed_existing_and_missing_ids` |
| AC-4 | `tests/test_autose_issue_1.py::test_ac4_remove_mixed_existing_and_missing_ids` |
| AC-5 | `tests/test_autose_issue_1.py::test_ac5_update_missing_ids_preserves_document` |
| AC-6 | `tests/test_autose_issue_1.py::test_ac6_remove_missing_ids_preserves_document` |

## Full suite

- Result: **pass**
- Counts: {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 10 new test(s) fail on base
