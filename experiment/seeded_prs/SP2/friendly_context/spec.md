# Spec — issue #3: `append` operation for list fields

## Summary

Add a built-in update operation `tinydb.operations.append(field, value)` that appends `value` to the list stored in `field` of every matching document, used with `Table.update` like the existing operations (`add`, `set`, `increment`, …). Documents without the field get a new list. The result must be persisted like any other update.

Issue type: **feature**

## Source excerpts

- **SRC-1:** "It would be nice to have this built in, as `tinydb.operations.append(field, value)`, used like the other operations"
- **SRC-2:** "if the document doesn't have the field yet, create it as a one-element list (`[value]`) instead of blowing up with a KeyError."
- **SRC-3:** "works with both `cond` and `doc_ids=` like the other operations, and obviously the change should be saved to the json file"

## Requirements

| ID | Requirement | Provenance | Sources |
|---|---|---|---|
| REQ-1 | `tinydb.operations.append(field, value)` exists and returns a transform usable with `Table.update`. | STATED | SRC-1 |
| REQ-2 | For a matching document whose `field` is a list, the value is added at the end of the list; non-matching documents are untouched. | STATED | SRC-1 |
| REQ-3 | If the document has no `field`, the field is created as a list containing the value. | STATED | SRC-2 |
| REQ-4 | Works with both `cond` and `doc_ids=`. | STATED | SRC-3 |
| REQ-5 | The change is persisted by the storage (e.g. JSON file). | STATED | SRC-3 |

## Acceptance criteria

- **AC-1** (REQ-1, REQ-2) — *Given* documents `{'name': 'ticket-41', 'tags': ['bug']}` and `{'name': 'ticket-42', 'tags': ['bug']}` — *when* `db.update(append('tags', 'urgent'), where('name') == 'ticket-42')` — *then* it returns `[2]`, document 2 has `tags == ['bug', 'urgent']` and document 1 still has `['bug']`. Repeated appends accumulate in order. *Observable:* return value, `get(doc_id=n)['tags']`.
- **AC-2** (REQ-3) — *Given* a document without `tags` — *when* `append('tags', 'urgent')` is applied — *then* its `tags` is `['urgent']` and no `KeyError` is raised. *Observable:* `get(...)['tags']`.
- **AC-3** (REQ-4) — *Given* two documents with `tags` — *when* `db.update(append('tags', 'wontfix'), doc_ids=[1])` — *then* only document 1 changes and `[1]` is returned. *Observable:* return value and documents.
- **AC-4** (REQ-5) — *Given* a JSON-file database — *when* two appends are applied and the database is reopened — *then* the list contains both values in order. *Observable:* document after reopening.

## Open questions

- **Q-1** (non-blocking): What if the field exists but is not a list (e.g. a string)? *Default:* not handled specially; the underlying error propagates, as with `increment` on a non-number.

## Out of scope

- Other list operations (remove, insert at index, deduplicate).
- Changes to `Table.update` itself.

## Injection findings

None.
