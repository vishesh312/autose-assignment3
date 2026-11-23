# Test report — issue #4

Rendered by the orchestrator from the pytest JSON report and `test_map.json`.

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest` | **233 passed**, 0 failed, 0 errors (0.28 s) |
| New tests | `python -m pytest tests/test_autose_issue_4.py` | 5 passed |
| Type check | `python -m mypy tinydb tests` | Success: no issues found in 20 source files |
| AC coverage | `pytest --collect-only` vs `test_map.json` | 5/5 ACs mapped to ≥1 collected test |

## AC → tests

| AC | Test | Result |
|---|---|---|
| AC-1 | `tests/test_autose_issue_4.py::test_ac1_limit_returns_first_n_matches_in_id_order` | passed |
| AC-2 | `tests/test_autose_issue_4.py::test_ac2_limit_none_is_the_default_and_returns_everything` | passed |
| AC-3 | `tests/test_autose_issue_4.py::test_ac3_fewer_matches_than_limit_returns_all_of_them` | passed |
| AC-4 | `tests/test_autose_issue_4.py::test_ac4_limit_on_named_table` | passed |
| AC-5 | `tests/test_autose_issue_4.py::test_ac5_limit_works_with_the_query_cache` | passed |

Attempts: Developer 1, Tester 1.
