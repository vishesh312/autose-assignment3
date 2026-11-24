# Test report: issue #3

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 1 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_3.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_3.py::test_ac1_append_to_existing_list`<br>`tests/test_autose_issue_3.py::test_ac1_append_multiple_items_preserves_order` |
| AC-2 | `tests/test_autose_issue_3.py::test_ac2_append_nested_list_to_empty_list`<br>`tests/test_autose_issue_3.py::test_ac2_append_nested_empty_list` |
| AC-3 | `tests/test_autose_issue_3.py::test_ac3_append_creates_missing_field`<br>`tests/test_autose_issue_3.py::test_ac3_append_missing_field_with_nested_list` |
| AC-4 | `tests/test_autose_issue_3.py::test_ac4_cond_updates_only_matching_document`<br>`tests/test_autose_issue_3.py::test_ac4_cond_no_match_leaves_documents_unchanged` |
| AC-5 | `tests/test_autose_issue_3.py::test_ac5_doc_ids_updates_only_selected_id`<br>`tests/test_autose_issue_3.py::test_ac5_doc_ids_empty_list_updates_nothing` |
| AC-6 | `tests/test_autose_issue_3.py::test_ac6_json_storage_persistence_after_reopen`<br>`tests/test_autose_issue_3.py::test_ac6_json_storage_missing_field_persisted` |

## Full suite

- Result: **pass**
- Counts: {"tests": 240, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 1 new test(s) fail on base
