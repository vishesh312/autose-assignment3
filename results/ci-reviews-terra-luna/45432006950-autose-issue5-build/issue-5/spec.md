# Spec: issue #5: Make membership checks work for document IDs and queries

# Issue 5: Membership checks

**Status: READY** — 3 of 3 requirements are ready; no blocking questions.

## Summary

Make `in` check document IDs and callable queries on TinyDB's default table and on named tables. Reject other operands with `TypeError`.

## Sources

- SRC-1: “checking if something is in the db is really clunky”
- SRC-2: “doc_id in table should be True if and only if a document with that (int) ID exists, i.e. exactly what table.contains(doc_id=doc_id) returns.”
- SRC-3: “query in table (anything callable, e.g. Query().email == x) should be True if and only if at least one document matches, i.e. exactly table.contains(query).”
- SRC-4: “Anything else (for example a dict / a document like {'name': 'alice'} in db) should raise a TypeError instead of silently returning a result.”
- SRC-5: “It has to work on both TinyDB (the default table) and on named tables from db.table('...').”
- SRC-6: “No new methods, no changes to contains() itself, and the speed of large tables is out of scope for this issue”
- SRC-7: “1 in db is True after the first insert and False again after db.remove(doc_ids=[1]).”

## Requirements

- **REQ-1 — CONFIRMED** (SRC-2, SRC-5, SRC-7): For an integer document ID, membership in a TinyDB instance or named table shall return the result of that table's `contains(doc_id=doc_id)` check.
- **REQ-2 — CONFIRMED** (SRC-3, SRC-5): For a callable query, membership in a TinyDB instance or named table shall return the result of that table's `contains(query)` check.
- **REQ-3 — CONFIRMED** (SRC-4, SRC-5): For an operand that is neither an integer document ID nor callable, membership in a TinyDB instance or named table shall raise `TypeError`.

## Acceptance criteria

- **AC-1 (REQ-1):** Given a new MemoryStorage database whose default table inserted `{'name': 'alice'}` as ID 1, when evaluating `1 in db`, then the result is `True`.
- **AC-2 (REQ-1):** Given a new MemoryStorage database whose default table inserted `{'name': 'alice'}` as ID 1 and then called `db.remove(doc_ids=[1])`, when evaluating `1 in db`, then the result is `False`.
- **AC-3 (REQ-1):** Given a new MemoryStorage database whose named `people` table inserted `{'name': 'alice'}` as ID 1, when evaluating `1 in db.table('people')`, then the result is `True`.
- **AC-4 (REQ-2):** Given a new MemoryStorage database whose default table contains `{'email': 'alice@example.com'}`, when evaluating `(Query().email == 'alice@example.com') in db`, then the result is `True`.
- **AC-5 (REQ-2):** Given a new MemoryStorage database whose named `people` table contains `{'email': 'alice@example.com'}`, when evaluating `(Query().email == 'bob@example.com') in db.table('people')`, then the result is `False`.
- **AC-6 (REQ-2):** Given a new MemoryStorage database whose named `people` table contains `{'name': 'alice'}`, when evaluating `(lambda doc: doc['name'] == 'alice') in db.table('people')`, then the result is `True`.
- **AC-7 (REQ-3):** Given a new MemoryStorage database whose default table contains `{'name': 'alice'}`, when evaluating `{'name': 'alice'} in db`, then `TypeError` is raised.
- **AC-8 (REQ-3):** Given a new MemoryStorage database whose named `people` table contains `{'name': 'alice'}`, when evaluating `{'name': 'alice'} in db.table('people')`, then `TypeError` is raised.

## Open questions and assumptions

None.

## Out of scope

New public methods, changes to `contains()`, large-table performance improvements, indexes, and exact-document membership semantics.

## Injection findings

None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A new TinyDB using MemoryStorage whose default table has just inserted {'name': 'alice'} as document ID 1. | Evaluate 1 in db. | The membership check reports that document ID 1 exists. | The expression returns True. | testable |
| AC-2 | A new TinyDB using MemoryStorage whose default table inserted {'name': 'alice'} as document ID 1 and then called db.remove(doc_ids=[1]). | Evaluate 1 in db. | The membership check reports that document ID 1 no longer exists. | The expression returns False. | testable |
| AC-3 | A new TinyDB using MemoryStorage with a named table db.table('people') that has inserted {'name': 'alice'} as document ID 1. | Evaluate 1 in db.table('people'). | The membership check reports that document ID 1 exists in the named table. | The expression returns True. | testable |
| AC-4 | A new TinyDB using MemoryStorage whose default table contains {'email': 'alice@example.com'}. | Evaluate (Query().email == 'alice@example.com') in db. | The membership check reports a matching document. | The expression returns True. | testable |
| AC-5 | A new TinyDB using MemoryStorage with a named table db.table('people') containing {'email': 'alice@example.com'}. | Evaluate (Query().email == 'bob@example.com') in db.table('people'). | The membership check reports that no document matches. | The expression returns False. | testable |
| AC-6 | A new TinyDB using MemoryStorage with a named table db.table('people') containing {'name': 'alice'}. | Evaluate (lambda doc: doc['name'] == 'alice') in db.table('people'). | The membership check evaluates the callable against the table's documents and reports a match. | The expression returns True. | testable |
| AC-7 | A new TinyDB using MemoryStorage whose default table contains {'name': 'alice'}. | Evaluate {'name': 'alice'} in db. | The membership check rejects the dictionary operand. | The expression raises TypeError. | testable |
| AC-8 | A new TinyDB using MemoryStorage with a named table db.table('people') containing {'name': 'alice'}. | Evaluate {'name': 'alice'} in db.table('people'). | The membership check rejects the dictionary operand. | The expression raises TypeError. | testable |

## Check

all criteria testable
