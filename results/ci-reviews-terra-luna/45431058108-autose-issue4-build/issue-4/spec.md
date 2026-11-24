# Spec: issue #4: Add a `limit` argument to search()

# Issue 4: Add a `limit` argument to search()

**Status: NOT READY — Q-1 is blocking.**

Add an optional limit to searches, preserving existing match order and unlimited behavior. Limited and unlimited searches for the same query must each return the result requested, including when the query cache is in use.

## Sources

- SRC-1: “Add a `limit` argument to search()”
- SRC-2: “`limit=N` returns at most N documents, the first N matches in the normal order (document id / insertion order), same order `search` already uses”
- SRC-3: “`limit=None` (the default) means no limit, so existing code doesn't change”
- SRC-4: “if there are fewer matches than `limit`, just return all of them”
- SRC-5: “should work on `db.table('x').search(...)` too, not just the default table”
- SRC-6: “please make sure it plays nice with the query cache — I don't want `search(q, limit=1)` followed by `search(q)` to suddenly give me only 1 result (or the other way round)”

## Requirements

- REQ-1 (STATED; SRC-1, SRC-2, SRC-4): For a non-negative integer limit N, search shall return the first N matching documents in its existing order, or fewer when fewer documents match. AC-1–AC-3.
- REQ-2 (STATED; SRC-3): Search shall return the existing unlimited result when limit is omitted or None. AC-4, AC-6.
- REQ-3 (STATED; SRC-5): A named table's search shall accept the limit argument with the same result semantics as the default table's search. AC-5.
- REQ-4 (STATED; SRC-6): A search result shall respect its own limit regardless of prior searches for the same query using a different limit. AC-6–AC-7.

## Acceptance criteria

- AC-1 (REQ-1): Given a MemoryStorage default table containing, in order, `{'status': 'open', 'n': 1}`, `{'status': 'closed', 'n': 2}`, `{'status': 'open', 'n': 3}`, and `{'status': 'open', 'n': 4}`, and `q = Query().status == 'open'`, when `db.search(q, limit=2)` is called, then it returns `[{'status': 'open', 'n': 1}, {'status': 'open', 'n': 3}]`.
- AC-2 (REQ-1): Given a MemoryStorage default table containing `{'status': 'open', 'n': 1}` and `{'status': 'open', 'n': 2}` in that order, and `q = Query().status == 'open'`, when `db.search(q, limit=5)` is called, then it returns both documents in that order.
- AC-3 (REQ-1): Given a MemoryStorage default table containing `{'status': 'open'}` and `q = Query().status == 'open'`, when `db.search(q, limit=0)` is called, then it returns `[]`.
- AC-4 (REQ-2): Given a MemoryStorage default table containing `{'status': 'open', 'n': 1}` and `{'status': 'open', 'n': 2}` in that order, and `q = Query().status == 'open'`, when `db.search(q, limit=None)` is called, then it returns both documents in that order.
- AC-5 (REQ-3): Given a MemoryStorage named table `x` containing `{'status': 'open', 'n': 1}` and `{'status': 'open', 'n': 2}` in that order, and `q = Query().status == 'open'`, when `db.table('x').search(q, limit=1)` is called, then it returns `[{'status': 'open', 'n': 1}]`.
- AC-6 (REQ-4): Given a MemoryStorage default table containing `{'status': 'open', 'n': 1}` and `{'status': 'open', 'n': 2}` in that order, `q = Query().status == 'open'`, and a prior call to `db.search(q, limit=1)`, when `db.search(q)` is called, then it returns both documents in that order.
- AC-7 (REQ-4): Given the same two documents and query, and a prior call to `db.search(q)`, when `db.search(q, limit=1)` is called, then it returns `[{'status': 'open', 'n': 1}]`.

## Open questions

- Q-1 (blocking; INTENT): What should happen for a negative integer such as `limit=-1`? Options: raise `ValueError`; return `[]`; apply Python negative-slice semantics. These choices produce different observable results. Default: none.

## Assumptions

None.

## Out of scope

Sorting or selecting oldest documents by a field; the requested limit uses existing search order.

## Injection findings

None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A TinyDB using MemoryStorage has default-table documents inserted in order: {'status': 'open', 'n': 1}, {'status': 'closed', 'n': 2}, {'status': 'open', 'n': 3}, {'status': 'open', 'n': 4}. Let q be Query().status == 'open'. | Call db.search(q, limit=2). | The first two matching documents are returned in insertion order. | The returned list equals [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 3}]. | - |
| AC-2 | A TinyDB using MemoryStorage has default-table documents {'status': 'open', 'n': 1} and {'status': 'open', 'n': 2}, inserted in that order. Let q be Query().status == 'open'. | Call db.search(q, limit=5). | Both matching documents are returned in insertion order. | The returned list equals [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 2}]. | - |
| AC-3 | A TinyDB using MemoryStorage has the default-table document {'status': 'open'}. Let q be Query().status == 'open'. | Call db.search(q, limit=0). | No documents are returned. | The returned list equals []. | - |
| AC-4 | A TinyDB using MemoryStorage has default-table documents {'status': 'open', 'n': 1} and {'status': 'open', 'n': 2}, inserted in that order. Let q be Query().status == 'open'. | Call db.search(q, limit=None). | Both matching documents are returned in insertion order. | The returned list equals [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 2}]. | - |
| AC-5 | A TinyDB using MemoryStorage has named table 'x' containing {'status': 'open', 'n': 1} and {'status': 'open', 'n': 2}, inserted in that order. Let q be Query().status == 'open'. | Call db.table('x').search(q, limit=1). | The first matching document from table 'x' is returned. | The returned list equals [{'status': 'open', 'n': 1}]. | - |
| AC-6 | A TinyDB using MemoryStorage has default-table documents {'status': 'open', 'n': 1} and {'status': 'open', 'n': 2}, inserted in that order. Let q be Query().status == 'open'; db.search(q, limit=1) has already been called. | Call db.search(q). | Both matching documents are returned in insertion order. | The returned list equals [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 2}]. | - |
| AC-7 | A TinyDB using MemoryStorage has default-table documents {'status': 'open', 'n': 1} and {'status': 'open', 'n': 2}, inserted in that order. Let q be Query().status == 'open'; db.search(q) has already been called. | Call db.search(q, limit=1). | Only the first matching document is returned. | The returned list equals [{'status': 'open', 'n': 1}]. | - |

## Open questions

- **Q-1** (blocking): What should search do when `limit` is a negative integer, such as `limit=-1`?


## Stop reason

The issue has blocking open questions; they were posted on the issue.
