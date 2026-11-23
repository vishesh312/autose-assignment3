# Spec — issue #1: update()/remove() with string doc_ids silently do nothing

## Summary

`Table.get` accepts document ids given as strings (`get(doc_id='1')`), but `Table.update(..., doc_ids=[...])` and `Table.remove(doc_ids=[...])` silently ignore the same string ids and return `[]`. They should accept exactly the ids that `get` accepts. Applies to the default table (`TinyDB`) and named tables, for every storage.

Issue type: **bug**

## Source excerpts

- **SRC-1:** "`update(..., doc_ids=[...])` and `remove(doc_ids=[...])` should accept the same ids that `get(doc_id=...)` / `get(doc_ids=[...])` accept, i.e. `'1'` should hit document 1 and the return value should be the list of ids that were actually updated/removed (`[1]`), same as with ints."
- **SRC-2:** "Ids that don't exist should still just be skipped like they are now with ints."
- **SRC-3:** "Same thing happens with a JSON file storage and with named tables (`db.table('foo')`)."

## Requirements

| ID | Requirement | Provenance | Sources |
|---|---|---|---|
| REQ-1 | `update(fields, doc_ids=ids)` updates every existing document whose id `get` would match for an element of `ids` (string or int) and returns those ids as ints. | STATED | SRC-1 |
| REQ-2 | `remove(doc_ids=ids)` removes every existing document whose id `get` would match and returns those ids as ints. | STATED | SRC-1 |
| REQ-3 | Ids that do not refer to an existing document are skipped without error, for both string and int ids. | STATED | SRC-2 |
| REQ-4 | The behaviour is the same for named tables and for JSON file storage. | STATED | SRC-3 |
| REQ-5 | Int ids keep working exactly as before. | DERIVED | SRC-1 |

## Acceptance criteria

- **AC-1** (REQ-1) — *Given* a table with documents 1, 2, 3 — *when* `update({'x': 10}, doc_ids=['1'])` is called — *then* it returns `[1]`, document 1 has `x == 10` and documents 2 and 3 are unchanged. *Observable:* return value and `get(doc_id=n)`.
- **AC-2** (REQ-2) — *Given* documents 1, 2, 3 — *when* `remove(doc_ids=['1', '3'])` is called — *then* it returns `[1, 3]` and only document 2 remains. *Observable:* return value, `len(db)`, `get`.
- **AC-3** (REQ-1, REQ-2, REQ-5) — *Given* documents 1, 2, 3 — *when* int and string ids are mixed (`doc_ids=[1, '2']`) — *then* both documents are affected and the return value contains ints. *Observable:* return value and document contents.
- **AC-4** (REQ-3) — *Given* documents 1, 2, 3 — *when* `update`/`remove` are called with ids `'42'` / `42` that don't exist — *then* they return `[]`, nothing changes and no exception is raised. *Observable:* return value, `len(db)`.
- **AC-5** (REQ-4) — *Given* a named table `things` in a JSON-file database — *when* string ids are used with `update` and `remove` and the database is reopened — *then* the changes are persisted. *Observable:* documents after reopening.

## Open questions

- **Q-1** (non-blocking): Should non-numeric strings such as `'abc'` raise? *Default:* no — treat them like any other id that doesn't exist (skip), which is what `get` does.

## Out of scope

- Changing `get`, `contains` or `insert` behaviour.
- Accepting other id types (floats, `Document` objects).

## Injection findings

None.
