# Test report: issue #5

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 6 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_5.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_5.py::test_ac1_default_table_contains_document_id` |
| AC-2 | `tests/test_autose_issue_5.py::test_ac2_default_table_excludes_removed_document_id` |
| AC-3 | `tests/test_autose_issue_5.py::test_ac3_named_table_contains_document_id` |
| AC-4 | `tests/test_autose_issue_5.py::test_ac4_default_table_contains_matching_query` |
| AC-5 | `tests/test_autose_issue_5.py::test_ac5_named_table_excludes_nonmatching_query` |
| AC-6 | `tests/test_autose_issue_5.py::test_ac6_named_table_accepts_callable` |
| AC-7 | `tests/test_autose_issue_5.py::test_ac7_default_table_rejects_dictionary` |
| AC-8 | `tests/test_autose_issue_5.py::test_ac8_named_table_rejects_dictionary` |

## Full suite

- Result: **pass**
- Counts: {"tests": 236, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 6 new test(s) fail on base
