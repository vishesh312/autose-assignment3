# Test report — issue #3

Rendered by the orchestrator from the pytest JSON report and `test_map.json`.

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest` | **233 passed**, 0 failed, 0 errors (0.25 s) |
| New tests | `python -m pytest tests/test_autose_issue_3.py` | 5 passed |
| Type check | `python -m mypy tinydb tests` | Success: no issues found in 20 source files |
| AC coverage | `pytest --collect-only` vs `test_map.json` | 4/4 ACs mapped to ≥1 collected test |

## AC → tests

| AC | Test | Result |
|---|---|---|
| AC-1 | `tests/test_autose_issue_3.py::test_ac1_append_adds_value_to_end_of_list` | passed |
| AC-1 | `tests/test_autose_issue_3.py::test_ac1_append_accumulates_over_multiple_updates` | passed |
| AC-2 | `tests/test_autose_issue_3.py::test_ac2_append_creates_list_when_field_missing` | passed |
| AC-3 | `tests/test_autose_issue_3.py::test_ac3_append_with_doc_ids` | passed |
| AC-4 | `tests/test_autose_issue_3.py::test_ac4_append_is_persisted_to_json_file` | passed |

Attempts: Developer 1, Tester 1.
