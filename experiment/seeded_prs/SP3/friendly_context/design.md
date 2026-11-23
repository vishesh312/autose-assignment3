# Design — issue #2

## Approach

The wrong results come from `Table.search` returning a cache entry that belongs to a different fragment query. The table is the component that owns the query cache, so the fix is made there: `Table.search` recognises fragment queries and evaluates them directly, skipping both the cache lookup and the cache store. All other queries keep using the cache unchanged. Fragment queries are detected from the query's structural description (the tuple `QueryInstance` keeps for hashing), walking nested `and`/`or`/`not` combinations so combined queries are covered too. `count` delegates to `search`, and `get(cond)` scans without the cache, so both are correct afterwards.

## Changes

| Path | Symbol | Kind | Description | ACs |
|---|---|---|---|---|
| `tinydb/table.py` | `Table._is_fragment_query` | new | Static helper; returns `True` if the query's description contains a `'fragment'` node, recursing into tuples and frozensets. | AC-1, AC-3 |
| `tinydb/table.py` | `Table.search` | modify | `use_cache = not self._is_fragment_query(cond)`; guard the cache lookup and the cache store with it. | AC-1, AC-2, AC-3, AC-4 |

## Public API

- No public signature changes. `Table.search`, `Table.count` and `Table.get` return correct results for fragment queries on any field.

## Test hooks

- `MemoryStorage`; documents with two nested dicts (`home`, `work`) sharing a sub-document.

## Risks

- Fragment queries are no longer cached; they are typically cheap relative to I/O, and correctness wins over caching here.
- Custom `QueryLike` objects without a `_hash` attribute: the helper falls back to "not a fragment" and caches them as before.

## Architecture references

- `ARCHITECTURE.md` — Table / query cache: `Table.search` owns the LRU query cache keyed by the query object; `count` is implemented via `search`.
