# Design — issue #3

## Approach

Add one function to `tinydb/operations.py`, following the pattern of the existing operations: `append(field, value)` returns a `transform(doc)` closure that mutates the document in place. `Table.update` already accepts callables, handles `cond`/`doc_ids` and writes through the storage, so no change is needed in `table.py` or `database.py`. Use `doc.setdefault(field, [])` so a missing field becomes a new list. Document the operation in `docs/usage.rst` next to the others.

## Changes

| Path | Symbol | Kind | Description | ACs |
|---|---|---|---|---|
| `tinydb/operations.py` | `append` | new | `append(field: str, value: Any) -> Callable[[MutableMapping], None]`; transform adds the value to `doc[field]`, creating the list if missing. | AC-1, AC-2, AC-3, AC-4 |
| `docs/usage.rst` | operations list | modify | Add a bullet for `append(key, value)`. | — |

## Public API

- `tinydb.operations.append(field: str, value: Any) -> Callable[[MutableMapping], None]` — to be passed to `Table.update` / `TinyDB.update`; adds `value` to the end of the list in `field`; creates the list if the field is missing.

## Test hooks

- `MemoryStorage` for behaviour; a `tmp_path` JSON database for persistence.

## Risks

- The field exists but holds a non-list value: out of scope (spec Q-1); an `AttributeError` propagates, consistent with other operations.

## Architecture references

- `ARCHITECTURE.md` — Operations: update operations are plain closures in `tinydb/operations.py`; `Table.update` applies them inside `_update_table`, which persists the result.
