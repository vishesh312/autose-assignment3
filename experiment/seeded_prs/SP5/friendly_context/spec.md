# Spec — issue #4: `limit` argument for search()

## Summary

Add an optional `limit` parameter to `Table.search` (and therefore `TinyDB.search`) that returns at most `limit` matching documents: the first matches in the normal document-ID order. `limit=None` is the default and means no limit. It must work on named tables and must work together with the query cache.

Issue type: **feature**

## Source excerpts

- **SRC-1:** "`limit=N` returns at most N documents, the first N matches in the normal order (document id / insertion order), same order `search` already uses"
- **SRC-2:** "`limit=None` (the default) means no limit, so existing code doesn't change"
- **SRC-3:** "if there are fewer matches than `limit`, just return all of them"
- **SRC-4:** "should work on `db.table('x').search(...)` too, not just the default table"
- **SRC-5:** "please make sure it plays nice with the query cache"

## Requirements

| ID | Requirement | Provenance | Sources |
|---|---|---|---|
| REQ-1 | `search(cond, limit=N)` returns the first N matches in document-ID order. | STATED | SRC-1 |
| REQ-2 | `limit` defaults to `None`, which returns all matches (unchanged behaviour). | STATED | SRC-2 |
| REQ-3 | With fewer than N matches, all matches are returned. | STATED | SRC-3 |
| REQ-4 | Works on named tables. | STATED | SRC-4 |
| REQ-5 | Limited searches work together with the query cache: a cached full result is not altered by a limited search and can still be served in full. | STATED | SRC-5 |

## Acceptance criteria

- **AC-1** (REQ-1) — *Given* 10 tasks with ids 1..10, odd ones `open` — *when* `search(Task.status == 'open', limit=3)` — *then* tasks 1, 3, 5 are returned in that order. *Observable:* returned documents and `doc_id`s.
- **AC-2** (REQ-2) — *Given* the same table — *when* `search(q)` and `search(q, limit=None)` — *then* both return all 5 open tasks, identical lists. *Observable:* returned documents.
- **AC-3** (REQ-3) — *Given* the same table — *when* `search(Task.status == 'done', limit=50)` — *then* all 5 done tasks are returned. *Observable:* returned documents.
- **AC-4** (REQ-4) — *Given* a named table `archive` with 4 open tasks — *when* `table.search(Task.status == 'open', limit=2)` — *then* the first 2 are returned. *Observable:* returned documents.
- **AC-5** (REQ-5) — *Given* `search(q)` has been run (result cached) — *when* `search(q, limit=2)` and then `search(q)` and `count(q)` run — *then* the limited call returns the first 2 matches and the later calls still return the full result. *Observable:* lengths and contents.

## Open questions

- **Q-1** (non-blocking): `limit=0` or negative values. *Default:* `limit=0` returns `[]`; negative values are not validated (issue leaves them open).

## Out of scope

- Offsets / pagination.
- `limit` on `get`, `count` or `contains`.

## Injection findings

None.
