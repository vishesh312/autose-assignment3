Implement the design for tinydb issue #4 on the current working tree.

Design (from stage 2):

<design>
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

</design>

Specification (from stage 1; the acceptance criteria are what the tests check):

<spec>
# Spec: issue #4: Add a `limit` argument to search()

# Issue 4: Add a `limit` argument to search()

**Status: READY** — no blocking questions.

## Summary

Add an optional search limit for the default table and named tables. Results retain the existing search order, and a previous search with a different limit must not change a later search's results.

## Sources

- SRC-1: “Could `search` take an optional `limit`?”
- SRC-2: “`limit=N` returns at most N documents, the first N matches in the normal order (document id / insertion order), same order `search` already uses”
- SRC-3: “`limit=None` (the default) means no limit, so existing code doesn't change”
- SRC-4: “if there are fewer matches than `limit`, just return all of them”
- SRC-5: “should work on `db.table('x').search(...)` too, not just the default table”
- SRC-6: “I don't want `search(q, limit=1)` followed by `search(q)` to suddenly give me only 1 result (or the other way round)”
- SRC-7: “a negative `limit` (e.g. `limit=-1`) should raise `ValueError`. `limit=0` returns an empty list.”

## Requirements

- REQ-1 (STATED; SRC-1, SRC-2, SRC-4, SRC-5): Searches on the default table and named tables shall accept an optional limit that returns at most that many matching documents in the existing search order.
- REQ-2 (STATED; SRC-3): A search with the limit omitted or set to None shall return all matches in the existing search order.
- REQ-3 (CONFIRMED; SRC-7): A search with a negative limit shall raise ValueError, and a search with limit zero shall return an empty list.
- REQ-4 (STATED; SRC-6): A search shall return the results specified by its own limit regardless of whether a previous search for the same query used a different limit.

## Acceptance criteria

- AC-1 (REQ-1): Given a MemoryStorage database with default-table documents {'status': 'open', 'n': 1}, {'status': 'closed', 'n': 2}, {'status': 'open', 'n': 3}, and {'status': 'open', 'n': 4}, in that order, and q = Query().status == 'open', when db.search(q, limit=2) is called, then it returns [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 3}].
- AC-2 (REQ-1): Given a MemoryStorage database with named table 'x' containing {'n': 1} and {'n': 2}, in that order, and q = Query().n > 0, when db.table('x').search(q, limit=5) is called, then it returns [{'n': 1}, {'n': 2}].
- AC-3 (REQ-2): Given a MemoryStorage database with default-table documents {'n': 1} and {'n': 2}, in that order, and q = Query().n > 0, when db.search(q, limit=None) is called, then it returns [{'n': 1}, {'n': 2}].
- AC-4 (REQ-3): Given a MemoryStorage database with default-table document {'n': 1} and q = Query().n > 0, when db.search(q, limit=0) is called, then it returns [].
- AC-5 (REQ-3): Given a MemoryStorage database with default-table document {'n': 1} and q = Query().n > 0, when db.search(q, limit=-1) is called, then it raises ValueError.
- AC-6 (REQ-4): Given a MemoryStorage database with the default query cache enabled, default-table documents {'n': 1} and {'n': 2} in that order, q = Query().n > 0, and a prior call to db.search(q, limit=1), when db.search(q) is called, then it returns [{'n': 1}, {'n': 2}].
- AC-7 (REQ-4): Given a MemoryStorage database with the default query cache enabled, default-table documents {'n': 1} and {'n': 2} in that order, q = Query().n > 0, and a prior call to db.search(q), when db.search(q, limit=1) is called, then it returns [{'n': 1}].

## Open questions and assumptions

None.

## Out of scope

Changes to sorting beyond preserving existing search order; behavior for limit values other than None and integers is unspecified.

## Injection findings

None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A TinyDB using MemoryStorage whose default table contains, in insertion order, {'status': 'open', 'n': 1}, {'status': 'closed', 'n': 2}, {'status': 'open', 'n': 3}, and {'status': 'open', 'n': 4}; q is Query().status == 'open'. | Call db.search(q, limit=2). | The first two matching documents are returned in insertion order. | The returned list equals [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 3}]. | testable |
| AC-2 | A TinyDB using MemoryStorage whose named table 'x' contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0. | Call db.table('x').search(q, limit=5). | Both matching documents are returned in insertion order. | The returned list equals [{'n': 1}, {'n': 2}]. | testable |
| AC-3 | A TinyDB using MemoryStorage whose default table contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0. | Call db.search(q, limit=None). | Both matching documents are returned in insertion order. | The returned list equals [{'n': 1}, {'n': 2}]. | testable |
| AC-4 | A TinyDB using MemoryStorage whose default table contains {'n': 1}; q is Query().n > 0. | Call db.search(q, limit=0). | The search returns no documents. | The returned value equals []. | testable |
| AC-5 | A TinyDB using MemoryStorage whose default table contains {'n': 1}; q is Query().n > 0. | Call db.search(q, limit=-1). | The search rejects the negative limit. | The call raises ValueError. | testable |
| AC-6 | A TinyDB using MemoryStorage with the default query cache enabled; its default table contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0; db.search(q, limit=1) has already been called. | Call db.search(q). | The unlimited search returns both matching documents in insertion order. | The returned list equals [{'n': 1}, {'n': 2}]. | testable |
| AC-7 | A TinyDB using MemoryStorage with the default query cache enabled; its default table contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0; db.search(q) has already been called. | Call db.search(q, limit=1). | The limited search returns only the first matching document. | The returned list equals [{'n': 1}]. | testable |

## Check

all criteria testable

</spec>

Retry context (empty on the first attempt; otherwise failing test output or reviewer `code` findings):

<retry_context>

</retry_context>

You must not create, modify or delete these paths (the diff is checked afterwards):

<forbidden_paths>
Anything outside: tinydb/**
In particular: tests/** (except the files above), .github/**, .autose/**, pyproject.toml, setup.py, setup.cfg, poetry.lock, uv.lock, pytest.ini, mypy.ini, tox.ini, .coveragerc, conftest.py, **/conftest.py, MANIFEST.in, ARCHITECTURE.md, CLAUDE.md, **/CLAUDE.md, .claude/**
</forbidden_paths>

Edit only files under `tinydb/`. Run compileall, mypy and the test suite before answering, then return the `dev_notes.json` object as your final answer.
