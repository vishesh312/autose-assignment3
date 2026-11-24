# Design

# Design: Support Membership Test Operator (`in`) for Table and TinyDB

## Approach
Currently, testing membership via `item in db` or `item in table` falls back to Python's default container iteration (`__iter__`), which compares each `Document` against `item`. For document IDs such as `1 in db`, this quietly returns `False` despite document 1 existing.

We address this by explicitly defining `__contains__(self, item: Any) -> bool` on both `Table` and `TinyDB`:
1. On `Table`: We inspect the operand type:
   - If `item` is an integer document ID (`isinstance(item, int) and not isinstance(item, bool)`), delegate directly to `self.contains(doc_id=item)`.
   - If `item` is callable (`callable(item)`), such as a `QueryInstance` (`where(...) == ...`) or a predicate function, delegate directly to `self.contains(cond=item)`.
   - For all other types (such as `dict`, `bool`, `str`, `list`, `float`, or `None`), raise a `TypeError`.
2. On `TinyDB`: We forward `item in db` to the default table instance by returning `item in self.table(self.default_table_name)`, following the exact pattern of `__len__` and `__iter__` in `database.py`.

This keeps `contains()` unchanged, does not alter storage or cache mechanics, and provides pythonic, safe membership testing across both database and table objects.

---

## Changes Table

| Path | Symbol | Kind | ACs |
|---|---|---|---|
| `tinydb/table.py` | `Table.__contains__` | new | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 |
| `tinydb/database.py` | `TinyDB.__contains__` | new | AC-1, AC-2, AC-3, AC-4, AC-5 |

---

## Public API & Test Hooks

### Public API

- **`Table.__contains__(self, item: Any) -> bool`**
  - **Behaviour:**
    - When evaluated via `doc_id in table` where `item` is an integer document ID (`isinstance(item, int)` and `not isinstance(item, bool)`), returns `True` if a document with that integer ID exists in the table, and `False` otherwise (equivalent to `table.contains(doc_id=item)`). If an existing document is removed (e.g., `table.remove(doc_ids=[doc_id])`), subsequent checks return `False`.
    - When evaluated via `query in table` where `item` is a callable query (`callable(item)`), returns `True` if at least one document in the table matches the query, and `False` otherwise (equivalent to `table.contains(query)`).
    - When evaluated with any other operand type that is neither an integer document ID nor a callable query (for example a `dict` document like `{'name': 'alice'}`, a `bool`, `str`, `list`, `float`, or `None`), raises `TypeError`.

- **`TinyDB.__contains__(self, item: Any) -> bool`**
  - **Behaviour:**
    - Forwards the membership test directly to the default table instance (`item in self.table(self.default_table_name)`).
    - Returns `True` if the integer document ID exists or if the callable query matches at least one document in the default table; returns `False` otherwise.
    - Raises `TypeError` if `item` is neither an integer document ID nor a callable query.

### Test Hooks
- **Object construction:**
  - `TinyDB` can be instantiated using `TinyDB(storage=MemoryStorage)` or via the `db` fixture in `tests/conftest.py`.
  - Named tables can be accessed via `db.table('<name>')` (e.g. `db.table('users')`).
- **Imports:**
  - `from tinydb import TinyDB, where, Query`
  - `from tinydb.storages import MemoryStorage, JSONStorage`
  - `import pytest`
- **Setup & Operations:**
  - `db.insert({'name': 'alice'})` inserts into the default table and returns document ID 1.
  - `table = db.table('users'); table.insert({'name': 'bob'})` inserts into a named table.
  - `db.remove(doc_ids=[1])` removes document 1.
  - Queries: `where('int') == 1` or `Query().int == 1`.
  - Membership syntax: `1 in db`, `1 in table`, `(where('int') == 1) in db`.
  - Type error assertion: `with pytest.raises(TypeError): {'name': 'alice'} in db`.

---

## Acceptance Criteria Traceability

- **AC-1** (`1 in db == True` after insert): Handled by `TinyDB.__contains__` forwarding to `Table.__contains__` returning `True` via `contains(doc_id=1)`.
- **AC-2** (`1 in db == False` after remove): Handled by `TinyDB.__contains__` forwarding to `Table.__contains__` returning `False` via `contains(doc_id=1)` after removal.
- **AC-3** (`(where('int') == 1) in db == True` when matching doc exists): Handled by `TinyDB.__contains__` forwarding to `Table.__contains__` returning `True` via `contains(cond=query)`.
- **AC-4** (`(where('int') == 2) in db == False` when no doc matches): Handled by `TinyDB.__contains__` forwarding to `Table.__contains__` returning `False` via `contains(cond=query)`.
- **AC-5** (`{'name': 'alice'} in db` raises `TypeError`): Handled by `Table.__contains__` raising `TypeError` for non-int non-callable operands; forwarded from `TinyDB.__contains__`.
- **AC-6** (`1 in db.table('users') == True` on named table): Handled directly by `Table.__contains__` on the named table instance.

---

## Architecture Constraints Considered

- **ARCHITECTURE.md §1 Overview:** `TinyDB` exposes default table operations and forwards magic methods (`__len__`, `__iter__`) manually because `__getattr__` does not intercept special dunder methods. Adding `TinyDB.__contains__` directly mirrors this established architecture.
- **ARCHITECTURE.md §3 Constraint 1 (Import direction):** `Table` does not import `TinyDB` or `database`. `database.py` already imports `Table`. No cross-boundary imports or circular dependencies are introduced.
- **ARCHITECTURE.md §3 Constraint 2 & 5 (Storage & Doc IDs):** Membership checks are read-only and delegate to existing `Table.contains()`, which uses `Table.get()` and respects string/int document ID translation across storage backends (`JSONStorage`, `MemoryStorage`).
- **ARCHITECTURE.md §3 Constraint 3 & 4 (Query cache & Hashing):** No storage writes occur, so query cache invalidation is unnecessary. `Table.get(cond)` evaluates conditions without mutating the query cache.

---

## Risks & Mitigations

1. **Boolean as integer sub-type:** In Python, `isinstance(True, int)` evaluates to `True`. Checking `isinstance(item, int) and not isinstance(item, bool)` prevents booleans from being misinterpreted as document IDs (0 or 1), ensuring `True in db` properly raises `TypeError`.
2. **Query exceptions:** Arbitrary callables passed to `in table` are evaluated as predicates. Any runtime error inside a user callable will propagate naturally, matching TinyDB's existing query evaluation behavior.
3. **No cache or storage side-effects:** Delegating to `Table.contains()` guarantees that no storage modifications or cache corruptions occur.

## Changes (machine-checked)

| Path | Symbol | Kind | ACs | Description |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.__contains__` | new | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 | In `tinydb/table.py`, add `from typing import Any` if not already present. Implement `Table.__contains__(self, item: Any) -> bool` (ideally following `__iter__` around line 743). If `isinstance(item, int) and not isinstance(item, bool)`, return `self.contains(doc_id=item)`. Elif `callable(item)`, return `self.contains(cond=item)`. Else, raise `TypeError(f'Invalid operand for membership test: expected int (doc_id) or callable (query), got {type(item).__name__}')`. This cleanly distinguishes integer doc IDs from callable queries, forbids booleans from being coerced to integer doc IDs, and prevents arbitrary types like dict documents from falling back to iteration. |
| `tinydb/database.py` | `TinyDB.__contains__` | new | AC-1, AC-2, AC-3, AC-4, AC-5 | In `tinydb/database.py`, add `from typing import Any` if not already present. Implement `TinyDB.__contains__(self, item: Any) -> bool` (following `__iter__` at line 274). Forward the membership check to the default table by returning `item in self.table(self.default_table_name)`. This provides uniform membership testing on the database instance matching `__len__` and `__iter__`. |

## Public API / test hooks

- `Table.__contains__(self, item: Any) -> bool`: Evaluates membership on the table instance using the `in` operator (`item in table`). If `item` is an integer document ID (`isinstance(item, int)` and not `bool`), returns `True` if a document with that ID exists in the table, and `False` otherwise (equivalent to `table.contains(doc_id=item)`). If the document was previously removed, returns `False`. If `item` is a callable query (`callable(item)`, such as a `QueryInstance` or function), returns `True` if at least one document in the table satisfies the query, and `False` otherwise (equivalent to `table.contains(query)`). If `item` is neither an integer doc ID nor a callable query (e.g. a `dict` document, `bool`, `str`, `list`, `float`, `None`), raises `TypeError`.
- `TinyDB.__contains__(self, item: Any) -> bool`: Evaluates membership on the TinyDB database instance using the `in` operator (`item in db`). Forwards the membership test directly to the default table instance (`item in self.table(self.default_table_name)`), behaving identically to `Table.__contains__` on the default table. Returns `True` if the integer document ID exists or if the callable query matches at least one document in the default table; returns `False` otherwise. Raises `TypeError` if `item` is neither an integer document ID nor a callable query.

Test hooks:
- Instantiate TinyDB with MemoryStorage (`TinyDB(storage=MemoryStorage)`) or JSONStorage (`TinyDB('path.json', storage=JSONStorage)`), or use the parameterized `db` fixture from `tests/conftest.py`.
- Access named tables via `db.table('<name>')` (e.g. `db.table('users')`).
- Import symbols from `tinydb` (`from tinydb import TinyDB, where, Query`) and `tinydb.storages` (`from tinydb.storages import MemoryStorage, JSONStorage`).
- Populate documents using `db.insert({'name': 'alice'})` or `db.table('users').insert({'name': 'bob'})`. Remove documents using `db.remove(doc_ids=[1])`.
- Construct queries using `where('field') == value` or `Query().field == value`.
- Exercise membership with `item in db` and `item in table`. Verify TypeError using `with pytest.raises(TypeError): <expression> in db`.

## Check

design checks passed
