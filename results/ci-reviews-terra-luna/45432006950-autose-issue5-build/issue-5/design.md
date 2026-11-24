# Design

## Approach

Add membership special methods to Table and TinyDB. Table dispatches integers and callables to the existing `contains()` method; TinyDB forwards the operation to its default table. Unsupported operands raise `TypeError`.

## Changes

| Path | Symbol | Kind | ACs |
| --- | --- | --- | --- |
| `tinydb/table.py` | `Table.__contains__` | new | AC-1–AC-8 |
| `tinydb/database.py` | `TinyDB.__contains__` | new | AC-1, AC-2, AC-4, AC-7 |

`Table.__contains__(self, item: object) -> bool` checks `isinstance(item, int)` first and calls `self.contains(doc_id=item)`. Otherwise it calls `self.contains(item)` for a callable, or raises `TypeError('Membership requires an integer document ID or a callable query')`. `TinyDB.__contains__(self, item: object) -> bool` returns `item in self.table(self.default_table_name)`.

## Public API and test hooks

Use `item in table` or `item in db`. Integers use ID lookup, callables use query lookup, and other operands raise `TypeError`. Exceptions from a callable propagate. Integer subclasses, including `bool`, use ID lookup; integer dispatch also takes precedence over callable dispatch.

Import `TinyDB` and `Query` from `tinydb` and `MemoryStorage` from `tinydb.storages`. Construct `TinyDB(storage=MemoryStorage)`, insert through `db` or `db.table('people')`, and exercise membership with IDs, query expressions, a lambda, and dictionaries.

## Traceability

- AC-1, AC-2: default-table ID membership uses both new special methods and existing `contains()`.
- AC-3: named-table ID membership uses `Table.__contains__`.
- AC-4: default-table query membership uses both new special methods.
- AC-5, AC-6: named-table query and lambda membership use `Table.__contains__`.
- AC-7: default-table dictionary membership forwards to `Table.__contains__` and raises `TypeError`.
- AC-8: named-table dictionary membership raises `TypeError` in `Table.__contains__`.

## Architecture constraints considered

No imports change (Constraint 1). Existing `contains()` and `get()` retain the whole-storage read and ID conversion paths (Constraints 2 and 5; ADR-1). No writes, query hashes, cache keys, or middleware construction are added (Constraints 3 and 4; ADR-2 and ADR-3).

## Risks

Python considers `bool` an `int`, so it follows the existing ID lookup behavior. Dictionary membership previously fell back to document iteration and equality; rejecting it is an intentional behavior change.

## Changes (machine-checked)

| Path | Symbol | Kind | ACs | Description |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.__contains__` | new | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 | Add def __contains__(self, item: object) -> bool alongside the existing special methods. First check isinstance(item, int) and return self.contains(doc_id=item); otherwise, if callable(item), return self.contains(item). For all other operands, raise TypeError('Membership requires an integer document ID or a callable query'). Integer dispatch takes precedence for objects that are both integers and callable. Do not alter contains(). |
| `tinydb/database.py` | `TinyDB.__contains__` | new | AC-1, AC-2, AC-4, AC-7 | Add def __contains__(self, item: object) -> bool alongside the existing forwarded special methods. Return item in self.table(self.default_table_name), so default-table membership uses the configured table class and propagates its result or exception. |

## Public API / test hooks

- `Table.__contains__(self, item: object) -> bool`: The expression item in table returns table.contains(doc_id=item) for an int, and table.contains(item) for any other callable. It raises TypeError for an operand that is neither an int nor callable. Exceptions raised by a callable propagate. Integer subclasses, including bool, follow the integer branch; an operand that is both an int and callable also follows that branch.
- `TinyDB.__contains__(self, item: object) -> bool`: The expression item in db has the same result or exception as item in db.table(db.default_table_name), including integer ID checks, callable query checks, and TypeError for unsupported operands.

Test hooks:
- Import TinyDB and Query from tinydb and MemoryStorage from tinydb.storages; construct a fresh database with TinyDB(storage=MemoryStorage).
- Use db.insert(...) and db.remove(doc_ids=[1]) for the default table; use db.table('people').insert(...) for a named table.
- Exercise membership with the Python in operator, including a Query expression, a plain lambda, and a dictionary operand.

## Check

design checks passed
