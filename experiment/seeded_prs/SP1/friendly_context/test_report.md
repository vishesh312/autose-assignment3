# Test report — issue #1

Rendered by the orchestrator from the pytest JSON report and `test_map.json`.

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest` | **235 passed**, 0 failed, 0 errors (0.27 s) |
| New tests | `python -m pytest tests/test_autose_issue_1.py` | 7 passed |
| Type check | `python -m mypy tinydb tests` | Success: no issues found in 20 source files |
| AC coverage | `pytest --collect-only` vs `test_map.json` | 5/5 ACs mapped to ≥1 collected test |

## AC → tests

| AC | Test | Result |
|---|---|---|
| AC-1 | `tests/test_autose_issue_1.py::test_ac1_update_with_string_doc_id_updates_document` | passed |
| AC-1 | `tests/test_autose_issue_1.py::test_ac1_update_with_string_doc_ids_and_callable` | passed |
| AC-2 | `tests/test_autose_issue_1.py::test_ac2_remove_with_string_doc_ids_removes_documents` | passed |
| AC-3 | `tests/test_autose_issue_1.py::test_ac3_mixed_int_and_string_ids` | passed |
| AC-3 | `tests/test_autose_issue_1.py::test_ac3_same_document_given_as_int_and_string` | passed |
| AC-4 | `tests/test_autose_issue_1.py::test_ac4_missing_ids_are_still_skipped` | passed |
| AC-5 | `tests/test_autose_issue_1.py::test_ac5_named_table_with_json_storage` | passed |

Attempts: Developer 1, Tester 1.
