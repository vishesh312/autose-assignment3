# Test report: issue #1

## Attempts

| # | Actor | Check | Result | Detail |
|---|---|---|---|---|
| 1 | developer | S3 build | pass | compileall, import and mypy passed |
| 2 | tester | S4 tester check | pass | AC mapping complete; 13 new test(s) fail on base |
| 3 | orchestrator | S4 suite + mypy | pass | suite passed {"tests": 243, "failures": 0, "errors": 0, "skipped": 0}; mypy passed |

## Acceptance criteria → tests (`tests/test_autose_issue_1.py`)

| AC | Tests |
|---|---|
| AC-1 | `tests/test_autose_issue_1.py::test_ac1_update_doc_id_string[default-memory]`<br>`tests/test_autose_issue_1.py::test_ac1_update_doc_id_string[default-json]`<br>`tests/test_autose_issue_1.py::test_ac1_update_doc_id_string[foo-memory]`<br>`tests/test_autose_issue_1.py::test_ac1_update_doc_id_string[foo-json]`<br>`tests/test_autose_issue_1.py::test_ac1_update_callable_with_string_id`<br>`tests/test_autose_issue_1.py::test_ac1_update_query_cache_invalidation` |
| AC-2 | `tests/test_autose_issue_1.py::test_ac2_remove_doc_id_string[default-memory]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_doc_id_string[default-json]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_doc_id_string[foo-memory]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_doc_id_string[foo-json]`<br>`tests/test_autose_issue_1.py::test_ac2_remove_query_cache_invalidation` |
| AC-3 | `tests/test_autose_issue_1.py::test_ac3_update_mixed_existing_and_nonexistent_ids` |
| AC-4 | `tests/test_autose_issue_1.py::test_ac4_remove_mixed_existing_and_nonexistent_ids` |
| AC-5 | `tests/test_autose_issue_1.py::test_ac5_update_all_nonexistent_ids` |
| AC-6 | `tests/test_autose_issue_1.py::test_ac6_remove_all_nonexistent_ids` |

## Full suite

- Result: **pass**
- Counts: {"tests": 243, "failures": 0, "errors": 0, "skipped": 0}

## Fails on base (anti-vacuous-test check)

- Result: **pass**: 13 new test(s) fail on base
