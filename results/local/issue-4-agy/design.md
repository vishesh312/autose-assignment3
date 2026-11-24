# Design

# Design Plan: Issue #4 - Add a `limit` argument to search()

## Approach
Extend `Table.search` with an optional `limit: Optional[int] = None` parameter. To maintain query cache isolation (REQ-4) without altering the `QueryLike` cache key or protocol (ADR-3, Constraint 4), the query cache continues to store the complete, unconstrained matching document list for a query. On cache hits, the cached list is sliced with `[:limit]`, producing a fresh list containing at most `limit` items (or all items if `limit is None`). On cache misses, all matching documents are evaluated, the full result list is cached in `_query_cache[cond]` if cacheable, and `docs[:limit]` is returned. `TinyDB.search` automatically gains this support via existing `__getattr__` attribute forwarding to the default table. This minimal change satisfies all acceptance criteria while preserving cache isolation and architecture invariants.

## Table of Changes
| Path | Symbol | Kind | ACs |
|---|---|---|---|
| `tinydb/table.py` | `Table.search` | `modify` | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 |

## Public API & Test Hooks

### Public API
- `Table.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`
  - **Behaviour**: Searches for documents matching the condition. When `limit` is a non-negative integer N, returns at most the first N matching documents in document ID order (or all matches if total matches <= N). When `limit=0`, returns an empty list `[]`. When `limit=None` (or omitted), returns all matching documents in document ID order without truncation. Query cache isolation is preserved between searches on the same condition with different limits or without limit, returning fresh list copies without result poisoning or truncation leakage across calls.
- `TinyDB.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`
  - **Behaviour**: Forwards to `Table.search` on the default table (`_default`) via `TinyDB.__getattr__`. When `limit` is a non-negative integer N, returns at most the first N matching documents in document ID order (or all matches if total matches <= N). When `limit=0`, returns an empty list `[]`. When `limit=None` (or omitted), returns all matching documents in document ID order without truncation. Query cache isolation is preserved between searches on the same condition with different limits or without limit.

### Test Hooks
- Import `TinyDB`, `where`, and `Query` from `tinydb`.
- Import `MemoryStorage` and `JSONStorage` from `tinydb.storages` (or `tinydb`).
- Construct an in-memory test database using `TinyDB(storage=MemoryStorage)` or use the `db` fixture from `tests/conftest.py`.
- Access specific named tables via `db.table('name')` (returns a `Table` instance), or access the default table directly via `db`.
- Method calls on `db` such as `db.search(...)` and `db.insert(...)` are forwarded via `__getattr__` to the default table `_default`.

## Traceability Matrix
- **AC-1** (`db.search(..., limit=2)` returns first 2 matches in order): Implemented by `Table.search` returning `docs[:2]` / `cached_results[:2]`.
- **AC-2** (`db.search(..., limit=5)` with fewer matches returns all matches): Implemented by Python list slicing `[:5]` returning all elements when length is less than 5.
- **AC-3** (`db.search(..., limit=0)` returns `[]`): Implemented by Python list slicing `[:0]` returning an empty list `[]`.
- **AC-4** (`db.search(..., limit=None)` preserves default search behavior): Implemented by Python list slicing `[:None]` returning all elements in a fresh list copy.
- **AC-5** (`db.table('tasks').search(..., limit=1)` works on non-default tables): Implemented directly in `Table.search`.
- **AC-6** (Cache isolation between limited and unlimited queries on same condition): Implemented by storing full result sets in `_query_cache[cond]` and slicing on return.

## Architecture Constraints Considered
- **ARCHITECTURE.md §1 Overview**: `TinyDB` forwards unknown methods to `_default` via `__getattr__`. Updating `Table.search` preserves this delegation without redundant method definitions in `database.py`.
- **ARCHITECTURE.md §2 ADR-3 & §3 Constraint 4**: The cache key remains `cond` (`QueryLike`) with its stable `_hash`. Storing full results in `_query_cache[cond]` keeps cache keys hashable and compatible with existing tests expecting `query in table._query_cache`.
- **ARCHITECTURE.md §3 Constraint 2**: Persistence interface remains intact; search continues to read storage via `_read_table()`.

## Risks
- **Result list mutation**: Slicing (`[:limit]` or `[:]`) always creates a new list instance, guaranteeing that mutations to returned lists by caller code do not alter cached results.
- **Table scan overhead**: Evaluating and caching full result sets scans the table even when `limit` is specified. Because TinyDB already performs full table scans for all queries (ADR-1, ADR-3), this aligns with existing architecture and allows subsequent queries with larger limits or no limit to hit the cache.
- **Negative limit values**: Per the spec, negative limits (e.g. `limit < 0`) are out of scope; standard non-negative integers and `None` are handled.
- **Security / prompt injection**: Reviewed spec and codebase comments for instructions directed at the agent or pipeline; none found.

## Changes (machine-checked)

| Path | Symbol | Kind | ACs | Description |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.search` | modify | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 | Add optional parameter `limit: Optional[int] = None` to `Table.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`. On query cache hit (`cached_results is not None`), return a slice `cached_results[:limit]`. On cache miss, scan `self._read_table().items()`, convert matching items to `self.document_class(doc, self.document_id_class(doc_id))`, store a shallow copy of the complete list into `self._query_cache[cond]` if `is_cacheable()`, and return `docs[:limit]`. In Python, slicing with `[:None]` returns all items in a fresh list, `[:0]` returns `[]`, and `[:limit]` with a positive integer returns at most the first `limit` items in insertion order without mutating the cached list. |

## Public API / test hooks

- `Table.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`: Searches for documents matching the given condition. When limit is a non-negative integer N, returns at most the first N matching documents in document ID order (or all matches if total matches <= N). When limit=0, returns an empty list []. When limit=None (or omitted), returns all matching documents in document ID order without truncation. Query caching ensures isolation between searches on the same condition with different limits or without limit, returning fresh list copies without result poisoning or truncation leakage across calls.
- `TinyDB.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`: Forwards to Table.search on the default table (_default) via TinyDB.__getattr__. When limit is a non-negative integer N, returns at most the first N matching documents in document ID order (or all matches if total matches <= N). When limit=0, returns an empty list []. When limit=None (or omitted), returns all matching documents in document ID order without truncation. Query cache isolation is preserved between searches on the same condition with different limits or without limit.

Test hooks:
- Import TinyDB, where, and Query from tinydb.
- Import MemoryStorage and JSONStorage from tinydb.storages (or tinydb).
- Construct an in-memory test database using TinyDB(storage=MemoryStorage) or use the db fixture from tests/conftest.py.
- Access specific named tables via db.table('name') (returns a Table instance), or access the default table directly via db.
- Method calls on db such as db.search(...) and db.insert(...) are forwarded via __getattr__ to the default table _default.

## Check

design checks passed
