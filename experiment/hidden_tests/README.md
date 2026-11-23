# Hidden acceptance tests

These tests are **never shown to the pipeline's agents**. They are kept outside the fork and run against the head of each AutoSE PR (or a local checkout of the PR branch) to measure whether the pipeline actually solved the issue.

| File | Issue |
|---|---|
| `test_issue_1.py` | #1 bug: `update`/`remove` ignore string `doc_ids` |
| `test_issue_2.py` | #2 bug: `fragment()` on different fields shares a query-cache entry |
| `test_issue_3.py` | #3 feature: `tinydb.operations.append` |
| `test_issue_4.py` | #4 feature: `search(cond, limit=N)` |
| `test_issue_5.py` | #5 vague: membership with `in`, as pinned down by `../issues/issue-5-maintainer-answer.md` |
| `reference/issue-N.patch` | Minimal reference fix for issue N (diff against `edff96a`). It is used **only** to check that the hidden tests can pass. It is never given to agents. |

The tests import only the public tinydb API (`TinyDB`, `Query`, `where`, `tinydb.storages.MemoryStorage`, `tinydb.operations`) plus pytest's `tmp_path`. They do not depend on private names or on exact error messages.

## How to run

```bash
REPO=/path/to/tinydb-checkout          # fork at edff96a, or a PR branch
HT=/path/to/autose-assignment3/experiment/hidden_tests

# one issue
PYTHONPATH=$REPO $REPO/.venv/bin/python -m pytest $HT/test_issue_1.py -p no:cacheprovider -o addopts=""

# all issues
PYTHONPATH=$REPO $REPO/.venv/bin/python -m pytest $HT -p no:cacheprovider -o addopts="" -rA
```

`-o addopts=""` turns off the repo's `pytest.ini` coverage options. `PYTHONPATH` makes sure that the checkout's `tinydb` is the one imported.

Reference validation, done in a scratch copy of the clean clone at `edff96a` (never in the fork):

```bash
cd $REPO
git apply $HT/reference/issue-N.patch                 # or: patch -p1 < ...
PYTHONPATH=$REPO .venv/bin/python -m pytest $HT/test_issue_N.py -p no:cacheprovider -o addopts=""
.venv/bin/python -m pytest -q                         # full existing suite
.venv/bin/python -m mypy tinydb                       # same check as upstream CI
git checkout -- tinydb
```

## Validation results (2026-11-24, Python 3.13.2, pytest 9, macOS)

| Issue | Hidden tests | At base `edff96a` | With reference patch | Existing suite + mypy with patch | Notes |
|---|---|---|---|---|---|
| 1 | `test_update_accepts_string_doc_ids`, `test_remove_accepts_string_doc_ids`, `test_string_ids_on_named_table_and_with_file_storage`, `test_int_ids_and_missing_string_ids_still_behave` | **3 failed, 1 passed** | 4 passed | 228 passed; mypy: no issues | The last test is a regression guard. It passes at base on purpose, because int IDs work and missing IDs are skipped (upstream #591), and both must keep working. |
| 2 | `test_search_fragment_on_two_fields_returns_own_results`, `test_count_and_get_with_fragment_on_other_field`, `test_fragment_queries_on_different_paths_are_not_equal` | **3 failed** | 3 passed | 228 passed; mypy: no issues | The third test checks query equality across paths. The issue explicitly reports `==` returning `True`. A "fix" that just makes `fragment` uncacheable would pass tests 1 and 2 but fail test 3, by design. |
| 3 | `test_append_adds_value_to_list_field_of_matching_docs`, `test_append_creates_list_when_field_missing`, `test_append_adds_list_as_single_element_and_accumulates`, `test_append_persists_to_json_file` | **4 failed** (ImportError) | 4 passed | 228 passed; mypy: no issues | The name `tinydb.operations.append(field, value)` is fixed by the issue text. |
| 4 | `test_limit_returns_first_n_matches_in_insertion_order`, `test_limit_does_not_poison_the_query_cache`, `test_limit_larger_than_matches_or_none_returns_everything`, `test_limit_on_named_table` | **4 failed** (TypeError: unexpected kwarg) | 4 passed | 228 passed; mypy: no issues | The cache test catches implementations that cache the truncated result. `limit=0` and negative limits are deliberately not tested, because the issue leaves them open. |
| 5 | `test_doc_id_membership_on_db_and_table`, `test_query_membership_on_db_and_table`, `test_membership_agrees_with_contains`, `test_unsupported_operand_raises_type_error` | **4 failed** | 4 passed | 228 passed; mypy: no issues | These test the maintainer's answer, not just the original vague text. Implementing `__contains__` only on `Table` fails the `db` assertions. |

All five reference patches also apply together cleanly. With all of them applied, the hidden suite gives `19 passed` and the existing suite gives `228 passed`.

Raw output summaries (from `pytest -q -rA`; the path prefix is trimmed):

```
##### issue 1 BASE
PASSED test_issue_1.py::test_int_ids_and_missing_string_ids_still_behave
FAILED test_issue_1.py::test_update_accepts_string_doc_ids
FAILED test_issue_1.py::test_remove_accepts_string_doc_ids
FAILED test_issue_1.py::test_string_ids_on_named_table_and_with_file_storage
3 failed, 1 passed in 0.04s
##### issue 1 REF
4 passed in 0.03s
##### issue 1 FULL SUITE + mypy
============================= 228 passed in 0.34s ==============================
Success: no issues found in 10 source files
##### issue 2 BASE
3 failed in 0.02s
##### issue 2 REF
3 passed in 0.00s
##### issue 2 FULL SUITE + mypy
============================= 228 passed in 0.34s ==============================
Success: no issues found in 10 source files
##### issue 3 BASE
4 failed in 0.01s
##### issue 3 REF
4 passed in 0.02s
##### issue 3 FULL SUITE + mypy
============================= 228 passed in 0.32s ==============================
Success: no issues found in 10 source files
##### issue 4 BASE
4 failed in 0.03s
##### issue 4 REF
4 passed in 0.00s
##### issue 4 FULL SUITE + mypy
============================= 228 passed in 0.29s ==============================
Success: no issues found in 10 source files
##### issue 5 BASE
4 failed in 0.02s
##### issue 5 REF
4 passed in 0.01s
##### issue 5 FULL SUITE + mypy
============================= 228 passed in 0.29s ==============================
Success: no issues found in 10 source files
##### all 5 patches applied together
19 passed in 0.03s   (hidden)   |   228 passed in 0.34s   (existing suite)
```
