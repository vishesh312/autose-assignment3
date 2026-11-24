# Design

## Approach

Add `limit` to `Table.search`. Keep complete results in the existing query cache and slice each returned list according to its own limit. Default-table calls reach the same method through `TinyDB` forwarding.

## Changes

| Path | Symbol | Kind | ACs |
|---|---|---|---|
| `tinydb/table.py` | `Table.search` | modify | AC-1–AC-7 |

Validate negative limits before cache access and raise `ValueError('limit must be non-negative')`; return `[]` for zero. For other limits, preserve the complete ordered search and cache behavior, then return a fresh slice using `[:limit]`. Update the method docstring.

## Public API and test hooks

`Table.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]` accepts positional or keyword limits. Omitted or `None` returns all matches, positive integers return the first matching documents up to the limit, zero returns an empty list, and negative integers raise `ValueError`. `TinyDB.search` forwards to this method for the default table; named tables expose it directly. Previous searches with another limit do not alter results.

Construct `TinyDB(storage=MemoryStorage)` using imports from `tinydb` and `tinydb.storages`; use `Query` from `tinydb`. Insert documents into the default table or `db.table('x')`. Returned `Document` objects compare equal to their corresponding dictionaries. Test both cache call orders with the same query.

## AC traceability

- AC-1, AC-2: ordered slicing supports default and named tables, including limits larger than the match count.
- AC-3: the `None` slice returns all matches.
- AC-4, AC-5: validation handles zero and negative limits.
- AC-6, AC-7: complete cached results are sliced separately for each call.

## Architecture and risks

ADR-1 and Constraint 2 retain whole-database reads; ADR-2 and Constraint 1 require no dependency changes. ADR-3 and Constraints 3–4 retain query cacheability and invalidation while caching full results. Constraint 5 retains existing document ID conversion. A limited cache miss still scans the whole table. Non-integer limits are outside the specification.

## Changes (machine-checked)

| Path | Symbol | Kind | ACs | Description |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.search` | modify | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7 | Add limit: Optional[int] = None after cond. Before consulting the cache, raise ValueError('limit must be non-negative') for a negative limit and return a new empty list for zero. On a cache hit, return cached_results[:limit]; Python's None slice returns the full fresh list. On a cache miss, retain the existing full ordered scan and Document/doc-ID conversion, cache a copy of the complete results only when the query is cacheable, and return docs[:limit]. Update the method docstring to describe the argument, ordering, zero and negative behavior, and complete-result caching. |

## Public API / test hooks

- `Table.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`: Returns matching Document objects in the existing search order. None or an omitted limit returns all matches; a positive integer returns at most that many, starting with the first match; zero returns an empty list; a negative integer raises ValueError. Each call applies its own limit regardless of prior searches for the same condition. The argument may be passed positionally or by keyword.
- `TinyDB.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`: Forwarded dynamically to the default table's Table.search, with the same return values, limit behavior, and ValueError for negative integers.

Test hooks:
- Import TinyDB and Query from tinydb and MemoryStorage from tinydb.storages; construct an empty database with TinyDB(storage=MemoryStorage).
- Use db.insert or db.insert_multiple for default-table documents and db.table('x').insert or insert_multiple for named-table documents. Document is a dict subclass, so returned lists can be compared directly with lists of dicts.
- The default query cache is enabled; exercise both limited-then-unlimited and unlimited-then-limited searches with the same query. Also exercise omitted and explicit None limits, zero, and a negative limit.
- TinyDB.search is provided by dynamic forwarding to the default table; named tables expose Table.search directly.

## Check

design checks passed
