# Test report: issue #3

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | builder | S3 build | pass | compileall, import and mypy passed |
| 2 | builder | S4 test check | pass | AC mapping complete; 1 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 235, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_3.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_3.py::test_ac1_append_existing_list` |
| AC-2 | `tests/test_autose_issue_3.py::test_ac2_append_nested_list` |
| AC-3 | `tests/test_autose_issue_3.py::test_ac3_append_missing_field`<br>`tests/test_autose_issue_3.py::test_ac3_append_missing_field_separate_instances` |
| AC-4 | `tests/test_autose_issue_3.py::test_ac4_append_with_cond` |
| AC-5 | `tests/test_autose_issue_3.py::test_ac5_append_with_doc_ids` |
| AC-6 | `tests/test_autose_issue_3.py::test_ac6_append_json_persistence` |

## Full suite

- Result: **pass**
- Counts: {"tests": 235, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 1 new test(s) fail on base
