## Summary

Makes existence checks pythonic, as agreed in the issue thread:

```python
1 in db                              # True iff document 1 exists  (== db.contains(doc_id=1))
(User.email == email) in db          # True iff any document matches (== db.contains(query))
{'name': 'alice'} in db              # TypeError instead of a silent result
```

Previously `1 in db` fell back to iterating the documents and comparing each one to `1`, so it was always `False`.

Closes {{ISSUE_REF}}

## Changes

- `tinydb/table.py`: new `Table.__contains__`. An `int` is treated as a document ID (`contains(doc_id=...)`), a callable as a query (`contains(cond)`); any other operand raises `TypeError`.
- `tinydb/database.py`: new `TinyDB.__contains__` forwarding to the default table (magic methods are not forwarded by `TinyDB.__getattr__`, same as `__len__`/`__iter__`).
- `contains()` itself is unchanged; no new public methods.
- `tests/test_autose_issue_5.py`: new tests for the four points in the maintainer's comment.

## Tests

| Acceptance criterion | Test(s) |
|---|---|
| AC-1 `doc_id in db` agrees with `contains(doc_id=...)`, also after removal | `test_ac1_doc_id_membership_matches_contains`, `test_ac1_removed_doc_id_is_no_longer_a_member` |
| AC-2 `query in db` agrees with `contains(query)` | `test_ac2_query_membership_matches_contains` |
| AC-3 unsupported operands are rejected | `test_ac3_unsupported_operand_is_rejected` |
| AC-4 works on named tables | `test_ac4_membership_on_named_table` |

- Full suite: **233 passed** (228 existing + 5 new)
- `mypy tinydb tests`: no issues

---
*Opened by AutoSE.*
