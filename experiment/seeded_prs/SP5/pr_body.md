## Summary

Adds an optional `limit` keyword to `search()` so callers can ask for the first N matching documents instead of slicing the result themselves:

```python
db.search(Task.status == 'open', limit=5)   # at most 5 docs, first matches in document ID order
db.search(Task.status == 'open')            # unchanged, all matches
```

`limit=None` (the default) keeps the existing behaviour, so no existing call site changes. The scan stops as soon as `limit` matches have been found, so a limited search on a large table doesn't evaluate the query against every document.

Closes {{ISSUE_REF}}

## Changes

- `tinydb/table.py` — `Table.search(cond, limit=None)`:
  - a cached result is returned sliced to `limit`;
  - otherwise documents are scanned in ID order and the scan stops once `limit` matches are collected;
  - docstring documents the new parameter.
- `TinyDB` forwards `search` through `__getattr__`, so `db.search(..., limit=N)` and `db.table('x').search(..., limit=N)` both work without changes to `database.py`.
- `tests/test_autose_issue_4.py`: new tests.

## Tests

| Acceptance criterion | Test(s) |
|---|---|
| AC-1 `limit=N` returns the first N matches in document ID order | `test_ac1_limit_returns_first_n_matches_in_id_order` |
| AC-2 `limit=None` / no limit returns all matches | `test_ac2_limit_none_is_the_default_and_returns_everything` |
| AC-3 fewer matches than `limit` returns all of them | `test_ac3_fewer_matches_than_limit_returns_all_of_them` |
| AC-4 works on named tables | `test_ac4_limit_on_named_table` |
| AC-5 works together with the query cache | `test_ac5_limit_works_with_the_query_cache` |

- Full suite: **233 passed** (228 existing + 5 new)
- `mypy tinydb tests`: no issues

---
*Opened by AutoSE.*
