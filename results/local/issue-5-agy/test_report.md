# Test report: issue #5

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 8 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_5.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_5.py::test_ac1_existing_doc_id_in_db`<br>`tests/test_autose_issue_5.py::test_ac1_multiple_doc_ids_in_db` |
| AC-2 | `tests/test_autose_issue_5.py::test_ac2_removed_doc_id_not_in_db`<br>`tests/test_autose_issue_5.py::test_ac2_never_inserted_doc_id_not_in_db` |
| AC-3 | `tests/test_autose_issue_5.py::test_ac3_matching_query_where_in_db`<br>`tests/test_autose_issue_5.py::test_ac3_matching_query_instance_or_callable_in_db` |
| AC-4 | `tests/test_autose_issue_5.py::test_ac4_non_matching_query_where_in_db`<br>`tests/test_autose_issue_5.py::test_ac4_non_matching_query_empty_db` |
| AC-5 | `tests/test_autose_issue_5.py::test_ac5_document_dict_raises_type_error`<br>`tests/test_autose_issue_5.py::test_ac5_invalid_types_raise_type_error` |
| AC-6 | `tests/test_autose_issue_5.py::test_ac6_named_table_contains_doc_id`<br>`tests/test_autose_issue_5.py::test_ac6_named_table_queries_and_removal` |

## Full suite

- Result: **pass**
- Counts: {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 8 new test(s) fail on base
