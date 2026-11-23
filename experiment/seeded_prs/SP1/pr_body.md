## Summary

`get(doc_id='1')` finds document 1, but `update(..., doc_ids=['1'])` and `remove(doc_ids=['1'])` silently matched nothing and returned `[]`, because they compared the requested ids directly against the integer table keys.

This PR makes `update()` and `remove()` look up `doc_ids` the same way `get()` does (by the id's string form), so `'1'` and `1` both refer to document 1.

Closes {{ISSUE_REF}}

## Changes

- `tinydb/table.py`
  - `Table.update` / `Table.remove`: requested ids are normalised with `str()` and resolved against the table through a new private helper `Table._existing_ids`, which mirrors the lookup in `get()`.
  - Ids that don't exist (including non-numeric strings) are still skipped silently, as before (#591 behaviour), and the return value is the list of **int** ids that were actually updated/removed.
  - A document passed twice in different forms (`[1, '1']`) is only updated/removed once.
  - Type hints for `doc_ids` widened to `Iterable[Union[int, str]]`; docstrings updated.
- `tests/test_autose_issue_1.py`: new tests (see below).

## Tests

| Acceptance criterion | Test(s) |
|---|---|
| AC-1 `update` with string ids updates the document and returns `[id]` | `test_ac1_update_with_string_doc_id_updates_document`, `test_ac1_update_with_string_doc_ids_and_callable` |
| AC-2 `remove` with string ids removes the documents and returns their ids | `test_ac2_remove_with_string_doc_ids_removes_documents` |
| AC-3 int and string ids can be mixed | `test_ac3_mixed_int_and_string_ids`, `test_ac3_same_document_given_as_int_and_string` |
| AC-4 missing ids are still skipped | `test_ac4_missing_ids_are_still_skipped` |
| AC-5 works on named tables with JSON storage | `test_ac5_named_table_with_json_storage` |

- Full suite: **235 passed** (228 existing + 7 new)
- `mypy tinydb tests`: no issues

---
*Opened by AutoSE.*
