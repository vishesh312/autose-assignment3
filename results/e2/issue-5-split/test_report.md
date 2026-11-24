# Test report: issue #5

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 7 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 239, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_5.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_5.py::test_ac1_in_db_doc_id_exists`<br>`tests/test_autose_issue_5.py::test_ac1_in_db_doc_id_missing` |
| AC-2 | `tests/test_autose_issue_5.py::test_ac2_in_db_doc_id_removed` |
| AC-3 | `tests/test_autose_issue_5.py::test_ac3_in_db_matching_query`<br>`tests/test_autose_issue_5.py::test_ac3_in_db_matching_query_instance_and_callable` |
| AC-4 | `tests/test_autose_issue_5.py::test_ac4_in_db_non_matching_query`<br>`tests/test_autose_issue_5.py::test_ac4_in_db_non_matching_callable` |
| AC-5 | `tests/test_autose_issue_5.py::test_ac5_in_db_doc_dict_raises_type_error`<br>`tests/test_autose_issue_5.py::test_ac5_in_db_invalid_types_raise_type_error` |
| AC-6 | `tests/test_autose_issue_5.py::test_ac6_in_named_table_doc_id_exists`<br>`tests/test_autose_issue_5.py::test_ac6_in_named_table_queries_and_invalid_types` |

## Full suite

- Result: **pass**
- Counts: {"tests": 239, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 7 new test(s) fail on base
