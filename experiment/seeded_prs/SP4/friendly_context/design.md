# Design — issue #5

## Approach

Implement `__contains__` on `Table`, dispatching on the operand type to the existing `contains()` method so the semantics are "exactly `contains`" by construction: `int` → `contains(doc_id=item)`, callable → `contains(item)`, anything else → `TypeError` with a short message. Because `TinyDB.__getattr__` does not forward magic methods, add `TinyDB.__contains__` that delegates to the default table, next to the existing `__len__`/`__iter__` forwarding. `contains()` is not modified.

## Changes

| Path | Symbol | Kind | Description | ACs |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.__contains__` | new | Dispatch int → `contains(doc_id=...)`, callable → `contains(cond)`, else raise `TypeError`. | AC-1, AC-2, AC-3, AC-4 |
| `tinydb/database.py` | `TinyDB.__contains__` | new | `return item in self.table(self.default_table_name)`. | AC-1, AC-2, AC-3 |

## Public API

- `item in table` / `item in db` → `bool`:
  - `int` item: `True` iff a document with that ID exists (same as `contains(doc_id=item)`).
  - callable item (e.g. a `Query`): `True` iff at least one document matches (same as `contains(item)`).
  - anything else: raises `TypeError`.

## Test hooks

- `MemoryStorage`; compare `in` with `contains()` directly; a named table via `db.table('people')`.

## Risks

- Previously `x in db` iterated documents and compared them to `x`; code relying on `document in db` will now get `TypeError`. This is the behaviour the maintainer asked for.

## Architecture references

- `ARCHITECTURE.md` — Database / Table: `TinyDB` forwards unknown attributes to the default table via `__getattr__`, but magic methods (`__len__`, `__iter__`) must be forwarded explicitly.
