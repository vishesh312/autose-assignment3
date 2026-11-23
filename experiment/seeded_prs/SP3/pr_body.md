## Summary

`db.search(Query().work.fragment({'city': 'Paris'}))` returned the cached result of an earlier `db.search(Query().home.fragment({'city': 'Paris'}))`, so `search`, `count` (and anything built on `search`) gave wrong answers for fragment queries on a second field. Calling the query directly was always correct; only the query cache served the wrong entry.

This PR makes `Table.search` evaluate fragment queries directly instead of going through the query cache, so each fragment query is always answered from the current table contents.

Closes {{ISSUE_REF}}

## Changes

- `tinydb/table.py`
  - New static helper `Table._is_fragment_query(cond)`: detects a `fragment()` query, including when it is combined with `&`, `|` or `~`.
  - `Table.search`: fragment queries skip both the cache lookup and the cache store. All other queries are cached exactly as before.
- `tests/test_autose_issue_2.py`: new tests.

## Tests

| Acceptance criterion | Test(s) |
|---|---|
| AC-1 `search` with a fragment on a second field returns that field's own matches, also on repeated calls | `test_ac1_search_fragment_on_second_field_is_correct`, `test_ac1_repeated_searches_stay_correct` |
| AC-2 `count` and `get` agree | `test_ac2_count_and_get_with_fragment_on_other_field` |
| AC-3 combined queries containing a fragment are correct | `test_ac3_fragment_combined_with_other_queries` |
| AC-4 results follow document updates | `test_ac4_results_follow_document_updates` |

- Full suite: **233 passed** (228 existing + 5 new)
- `mypy tinydb tests`: no issues

---
*Opened by AutoSE.*
