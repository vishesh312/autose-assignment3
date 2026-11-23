## Summary

Adds `tinydb.operations.append(field, value)`, a built-in update operation for list fields, used like the existing operations:

```python
from tinydb.operations import append

db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
# {'name': 'ticket-42', 'tags': ['bug']}  ->  {'name': 'ticket-42', 'tags': ['bug', 'urgent']}
```

If a document doesn't have the field yet, it is created as a new list instead of raising `KeyError`, so older documents without `tags` work too.

Closes {{ISSUE_REF}}

## Changes

- `tinydb/operations.py`: new `append(field, value)` operation (same shape as `add`/`set`: returns a `transform(doc)` callable).
- `docs/usage.rst`: listed `append` with the other built-in operations.
- `tests/test_autose_issue_3.py`: new tests.

## Tests

| Acceptance criterion | Test(s) |
|---|---|
| AC-1 appends the value to the end of the list of matching documents only | `test_ac1_append_adds_value_to_end_of_list`, `test_ac1_append_accumulates_over_multiple_updates` |
| AC-2 a missing field is created as a list | `test_ac2_append_creates_list_when_field_missing` |
| AC-3 works with `doc_ids=` as well as a condition | `test_ac3_append_with_doc_ids` |
| AC-4 the change is persisted to the JSON file | `test_ac4_append_is_persisted_to_json_file` |

- Full suite: **233 passed** (228 existing + 5 new)
- `mypy tinydb tests`: no issues

---
*Opened by AutoSE.*
