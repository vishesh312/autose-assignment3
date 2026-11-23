# Design — issue #1

## Approach

`get()` looks documents up by `str(doc_id)` against the raw table, while `update()`/`remove()` compare the requested ids directly with the keys of the converted table, which are `document_id_class` (int) instances. `'1' in {1: ...}` is `False`, so string ids silently match nothing.

Fix it at the point where the requested ids are matched against the table: normalise each requested id with `str()` and resolve it against the string form of the table keys, exactly like `get()`. Both code paths share one private helper so they cannot drift apart. The existing #591 semantics are preserved: unknown ids are skipped and the return value lists only the ids actually touched (as table keys, i.e. ints).

## Changes

| Path | Symbol | Kind | Description | ACs |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.update` | modify | Build `requested_ids` as `str(doc_id)`; inside the updater resolve them with `_existing_ids`. Widen the type hint to `Iterable[Union[int, str]]`. | AC-1, AC-3, AC-4, AC-5 |
| `tinydb/table.py` | `Table.remove` | modify | Same change as `update`. | AC-2, AC-3, AC-4, AC-5 |
| `tinydb/table.py` | `Table._existing_ids` | new | Static helper: map `str(key) -> key` for the table, return the keys for the requested ids in request order, skipping unknown ids and duplicates. | AC-1 … AC-4 |

## Public API

- `Table.update(fields, cond=None, doc_ids: Optional[Iterable[Union[int, str]]] = None) -> list[int]` — string ids are accepted and refer to the same document as the int id; unknown ids are skipped.
- `Table.remove(cond=None, doc_ids: Optional[Iterable[Union[int, str]]] = None) -> list[int]` — same.
- `TinyDB` forwards both through `__getattr__`; no change needed in `database.py`.

## Test hooks

- `MemoryStorage` for most tests; one test with a JSON file and a named table, reopened to check persistence.

## Risks

- Duplicate ids in the request (`[1, '1']`) would now resolve to the same key twice; `remove` would then `del` the same key twice. The helper deduplicates to avoid a `KeyError`.
- Custom `document_id_class` implementations: the helper only relies on `str(key)`, the same assumption `get()` already makes.

## Architecture references

- `ARCHITECTURE.md` — Table: documents are stored with string keys in the storage layer and converted to `document_id_class` in `Table._read_table`; read paths (`get`) look up by `str(doc_id)`.
