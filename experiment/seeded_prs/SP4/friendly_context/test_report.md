# Test report — issue #5

Rendered by the orchestrator from the pytest JSON report and `test_map.json`.

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest` | **233 passed**, 0 failed, 0 errors (0.28 s) |
| New tests | `python -m pytest tests/test_autose_issue_5.py` | 5 passed |
| Type check | `python -m mypy tinydb tests` | Success: no issues found in 20 source files |
| AC coverage | `pytest --collect-only` vs `test_map.json` | 4/4 ACs mapped to ≥1 collected test |

## AC → tests

| AC | Test | Result |
|---|---|---|
| AC-1 | `tests/test_autose_issue_5.py::test_ac1_doc_id_membership_matches_contains` | passed |
| AC-1 | `tests/test_autose_issue_5.py::test_ac1_removed_doc_id_is_no_longer_a_member` | passed |
| AC-2 | `tests/test_autose_issue_5.py::test_ac2_query_membership_matches_contains` | passed |
| AC-3 | `tests/test_autose_issue_5.py::test_ac3_unsupported_operand_is_rejected` | passed |
| AC-4 | `tests/test_autose_issue_5.py::test_ac4_membership_on_named_table` | passed |

Attempts: Developer 1, Tester 1.
