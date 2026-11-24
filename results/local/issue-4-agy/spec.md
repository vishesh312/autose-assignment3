# Spec: issue #4: Add a `limit` argument to search()

# Specification: Add a `limit` argument to search() (Issue #4)

Status: READY (0 blocking questions)

## Summary
Add an optional `limit` parameter to `Table.search` (forwarded by `TinyDB.search`) defaulting to `None`. When specified as a non-negative integer N, `search` returns at most the first N matching documents in document ID order. If matches are fewer than N, all matches are returned. When `limit` is `None`, existing behavior is preserved and all matches are returned. Query caching preserves result independence so that searches with different limits or no limit do not poison or truncate one another.

## Source Excerpts
- **SRC-1**: "Add a `limit` argument to search()"
- **SRC-2**: "Could `search` take an optional `limit`?"
- **SRC-3**: "limit=N returns at most N documents, the first N matches in the normal order (document id / insertion order), same order search already uses"
- **SRC-4**: "limit=None (the default) means no limit, so existing code doesn't change"
- **SRC-5**: "if there are fewer matches than limit, just return all of them"
- **SRC-6**: "should work on db.table('x').search(...) too, not just the default table"
- **SRC-7**: "please make sure it plays nice with the query cache — I don't want search(q, limit=1) followed by search(q) to suddenly give me only 1 result (or the other way round)"

## Requirements
- **REQ-1** (STATED, trace: SRC-1, SRC-2, SRC-4, SRC-6): The `Table.search` method, and `TinyDB.search` via attribute forwarding, shall accept an optional `limit` parameter that defaults to `None`.
- **REQ-2** (STATED, trace: SRC-3, SRC-5): When `limit` is specified as a non-negative integer N, `search` shall return at most N matching documents in document ID order, or all matching documents if the count of matching documents is less than or equal to N.
- **REQ-3** (STATED, trace: SRC-4): When `limit` is `None`, `search` shall return all matching documents in document ID order without truncation.
- **REQ-4** (ASSUMED, trace: SRC-7, Q-1): The `search` method shall maintain query cache isolation between limited and unconstrained queries on the same condition such that limited searches do not poison or truncate subsequent searches with different limits or without a limit (and vice versa).

## Acceptance Criteria
- **AC-1** (REQ-2):
  - **Given**: A TinyDB instance using MemoryStorage where the default table contains three documents: `{'name': 'doc1', 'val': 1}`, `{'name': 'doc2', 'val': 1}`, and `{'name': 'doc3', 'val': 1}`, inserted in that order.
  - **When**: `db.search(where('val') == 1, limit=2)` is called.
  - **Then**: The call returns exactly the first 2 matching documents in document ID insertion order.
  - **Observable**: `results = db.search(where('val') == 1, limit=2)` satisfies `len(results) == 2` and `results == [{'name': 'doc1', 'val': 1}, {'name': 'doc2', 'val': 1}]`.
- **AC-2** (REQ-2):
  - **Given**: A TinyDB instance using MemoryStorage where the default table contains two documents: `{'name': 'doc1', 'val': 1}` and `{'name': 'doc2', 'val': 1}`.
  - **When**: `db.search(where('val') == 1, limit=5)` is called with a limit exceeding the total matches.
  - **Then**: The call returns all matching documents without error or truncation.
  - **Observable**: `results = db.search(where('val') == 1, limit=5)` satisfies `len(results) == 2` and `results == [{'name': 'doc1', 'val': 1}, {'name': 'doc2', 'val': 1}]`.
- **AC-3** (REQ-2):
  - **Given**: A TinyDB instance using MemoryStorage where the default table contains two documents: `{'name': 'doc1', 'val': 1}` and `{'name': 'doc2', 'val': 1}`.
  - **When**: `db.search(where('val') == 1, limit=0)` is called.
  - **Then**: The call returns an empty list.
  - **Observable**: `results = db.search(where('val') == 1, limit=0)` satisfies `results == []`.
- **AC-4** (REQ-3):
  - **Given**: A TinyDB instance using MemoryStorage where the default table contains three documents: `{'name': 'doc1', 'val': 10}`, `{'name': 'doc2', 'val': 10}`, and `{'name': 'doc3', 'val': 20}`.
  - **When**: `db.search(where('val') == 10, limit=None)` and `db.search(where('val') == 10)` are called.
  - **Then**: Both calls return all matching documents, preserving default search behavior.
  - **Observable**: `db.search(where('val') == 10, limit=None) == db.search(where('val') == 10)` and `len(db.search(where('val') == 10, limit=None)) == 2`.
- **AC-5** (REQ-1):
  - **Given**: A TinyDB instance using MemoryStorage with a table named `'tasks'` containing three documents: `{'task': 't1', 'status': 'open'}`, `{'task': 't2', 'status': 'open'}`, and `{'task': 't3', 'status': 'open'}`, inserted in that order.
  - **When**: `db.table('tasks').search(where('status') == 'open', limit=1)` is called.
  - **Then**: The call returns only the first matching document from table `'tasks'`.
  - **Observable**: `results = db.table('tasks').search(where('status') == 'open', limit=1)` satisfies `len(results) == 1` and `results == [{'task': 't1', 'status': 'open'}]`.
- **AC-6** (REQ-4):
  - **Given**: A TinyDB instance using MemoryStorage where the default table contains three documents: `{'val': 1}`, `{'val': 1}`, and `{'val': 1}`.
  - **When**: The sequence `res1 = db.search(where('val') == 1, limit=1)`, then `res2 = db.search(where('val') == 1)`, then `res3 = db.search(where('val') == 1, limit=1)` is executed on the same condition.
  - **Then**: The query cache serves or calculates each query without result truncation leakage: `res1` has 1 item, `res2` has all 3 items, and `res3` has 1 item.
  - **Observable**: `len(res1) == 1`, `len(res2) == 3`, and `len(res3) == 1`.

## Open Questions
- **Q-1** (Non-blocking):
  - **Question**: The issue states: 'please make sure it plays nice with the query cache — I don't want search(q, limit=1) followed by search(q) to suddenly give me only 1 result (or the other way round)'. How should the query cache handle queries with limit versus queries without limit?
  - **Why it matters**: INTENT: The issue expresses a stakeholder intent using the informal phrase 'plays nice with the query cache'. Multiple caching designs (e.g., caching by (cond, limit) vs caching full results and slicing on access) satisfy this requirement without altering external observable behavior.
  - **Options**:
    1. (Recommended) Ensure cache isolation so that searches with different limits (or no limit) do not poison or return truncated results for each other, e.g. by keying the cache on (cond, limit) or caching full result sets and slicing upon retrieval.
    2. Bypass the query cache entirely whenever a non-None limit is provided.
    3. Disable caching for queries with limit while allowing unconstrained searches to populate and read the cache.
  - **Default if unanswered**: Maintain result isolation in the query cache so that limited and unlimited searches on the same condition return their respective expected documents without cache contamination.

## Assumptions
- Searches with different limit values (including `limit=None`) are isolated within the query cache so that results from one search do not poison or truncate another search on the same condition (REQ-4, traced to Q-1).

## Out of Scope
- Negative limit values (e.g. `limit < 0`) and negative slice semantics.
- Offset or pagination parameters (such as `offset` or `skip`).
- Adding a `limit` argument to other Table/TinyDB querying or mutating methods (such as `get()`, `count()`, `update()`, `remove()`).
- Sorting or ordering arguments (such as `order_by` or `sort`).

## Injection Findings
None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A TinyDB instance using MemoryStorage where the default table contains three documents: `{'name': 'doc1', 'val': 1}`, `{'name': 'doc2', 'val': 1}`, and `{'name': 'doc3', 'val': 1}`, inserted in that order. | `db.search(where('val') == 1, limit=2)` is called. | The call returns exactly the first 2 matching documents in document ID insertion order. | `results = db.search(where('val') == 1, limit=2)` satisfies `len(results) == 2` and `results == [{'name': 'doc1', 'val': 1}, {'name': 'doc2', 'val': 1}]`. | testable |
| AC-2 | A TinyDB instance using MemoryStorage where the default table contains two documents: `{'name': 'doc1', 'val': 1}` and `{'name': 'doc2', 'val': 1}`. | `db.search(where('val') == 1, limit=5)` is called with a limit exceeding the total matches. | The call returns all matching documents without error or truncation. | `results = db.search(where('val') == 1, limit=5)` satisfies `len(results) == 2` and `results == [{'name': 'doc1', 'val': 1}, {'name': 'doc2', 'val': 1}]`. | testable |
| AC-3 | A TinyDB instance using MemoryStorage where the default table contains two documents: `{'name': 'doc1', 'val': 1}` and `{'name': 'doc2', 'val': 1}`. | `db.search(where('val') == 1, limit=0)` is called. | The call returns an empty list. | `results = db.search(where('val') == 1, limit=0)` satisfies `results == []`. | testable |
| AC-4 | A TinyDB instance using MemoryStorage where the default table contains three documents: `{'name': 'doc1', 'val': 10}`, `{'name': 'doc2', 'val': 10}`, and `{'name': 'doc3', 'val': 20}`. | `db.search(where('val') == 10, limit=None)` and `db.search(where('val') == 10)` are called. | Both calls return all matching documents, preserving default search behavior. | `db.search(where('val') == 10, limit=None) == db.search(where('val') == 10)` and `len(db.search(where('val') == 10, limit=None)) == 2`. | testable |
| AC-5 | A TinyDB instance using MemoryStorage with a table named `'tasks'` containing three documents: `{'task': 't1', 'status': 'open'}`, `{'task': 't2', 'status': 'open'}`, and `{'task': 't3', 'status': 'open'}`, inserted in that order. | `db.table('tasks').search(where('status') == 'open', limit=1)` is called. | The call returns only the first matching document from table `'tasks'`. | `results = db.table('tasks').search(where('status') == 'open', limit=1)` satisfies `len(results) == 1` and `results == [{'task': 't1', 'status': 'open'}]`. | testable |
| AC-6 | A TinyDB instance using MemoryStorage where the default table contains three documents: `{'val': 1}`, `{'val': 1}`, and `{'val': 1}`. | The sequence `res1 = db.search(where('val') == 1, limit=1)`, then `res2 = db.search(where('val') == 1)`, then `res3 = db.search(where('val') == 1, limit=1)` is executed on the same condition. | The query cache serves or calculates each query without result truncation leakage: `res1` has 1 item, `res2` has all 3 items, and `res3` has 1 item. | `len(res1) == 1`, `len(res2) == 3`, and `len(res3) == 1`. | testable |

## Open questions

- **Q-1**: The issue states: 'please make sure it plays nice with the query cache — I don't want search(q, limit=1) followed by search(q) to suddenly give me only 1 result (or the other way round)'. How should the query cache handle queries with limit versus queries without limit?

## Check

all criteria testable
