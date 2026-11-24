# Test report: issue #5

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | builder | S3 build | pass | compileall, import and mypy passed |
| 2 | builder | S4 test check | pass | AC mapping complete; 4 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 234, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_5.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_5.py::test_ac1_doc_id_exists` |
| AC-2 | `tests/test_autose_issue_5.py::test_ac2_doc_id_removed` |
| AC-3 | `tests/test_autose_issue_5.py::test_ac3_query_matches` |
| AC-4 | `tests/test_autose_issue_5.py::test_ac4_query_no_match` |
| AC-5 | `tests/test_autose_issue_5.py::test_ac5_invalid_operand_type_error` |
| AC-6 | `tests/test_autose_issue_5.py::test_ac6_named_table_membership` |

## Full suite

- Result: **pass**
- Counts: {"tests": 234, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 4 new test(s) fail on base
