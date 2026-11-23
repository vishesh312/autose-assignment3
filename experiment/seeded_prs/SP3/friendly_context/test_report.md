# Test report — issue #2

Rendered by the orchestrator from the pytest JSON report and `test_map.json`.

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest` | **233 passed**, 0 failed, 0 errors (0.27 s) |
| New tests | `python -m pytest tests/test_autose_issue_2.py` | 5 passed |
| Type check | `python -m mypy tinydb tests` | Success: no issues found in 20 source files |
| AC coverage | `pytest --collect-only` vs `test_map.json` | 4/4 ACs mapped to ≥1 collected test |

## AC → tests

| AC | Test | Result |
|---|---|---|
| AC-1 | `tests/test_autose_issue_2.py::test_ac1_search_fragment_on_second_field_is_correct` | passed |
| AC-1 | `tests/test_autose_issue_2.py::test_ac1_repeated_searches_stay_correct` | passed |
| AC-2 | `tests/test_autose_issue_2.py::test_ac2_count_and_get_with_fragment_on_other_field` | passed |
| AC-3 | `tests/test_autose_issue_2.py::test_ac3_fragment_combined_with_other_queries` | passed |
| AC-4 | `tests/test_autose_issue_2.py::test_ac4_results_follow_document_updates` | passed |

Attempts: Developer 1, Tester 1.
