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
