# Design — issue #4

## Approach

Add `limit: Optional[int] = None` to `Table.search`. When the cache already holds the full result for `cond`, return it sliced with `[:limit]` (slicing with `None` returns everything, so the default path is unchanged). On a cache miss, scan the table in document-ID order and stop as soon as `limit` matches have been collected, so a limited search on a large table doesn't evaluate the query against every remaining document. The existing cacheability logic after the scan is kept as is. `TinyDB.search` is forwarded via `__getattr__`, so `database.py` needs no change.

## Changes

| Path | Symbol | Kind | Description | ACs |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.search` | modify | New `limit` parameter; slice cached results; replace the list comprehension with a loop that breaks once `limit` matches are collected; document the parameter. | AC-1, AC-2, AC-3, AC-4, AC-5 |

## Public API

- `Table.search(cond: QueryLike, limit: Optional[int] = None) -> list[Document]` — at most `limit` documents, the first matches in document-ID order; `None` means no limit. Also available as `TinyDB.search(...)`.

## Test hooks

- `MemoryStorage`; 10 documents with an alternating `status`; a named table; call `search(q)` before `search(q, limit=N)` to exercise the cache path.

## Risks

- Interaction with the query cache: cached results are sliced on the way out, so the cached list itself is never shortened by a limited call.
- `limit=0`: the loop breaks before evaluating any document and returns `[]`.

## Architecture references

- `ARCHITECTURE.md` — Table / query cache: `Table.search` serves repeated identical queries from an LRU cache keyed by the query and stores a copy of the result for cacheable queries.
