Implement the design for tinydb issue #5 on the current working tree.

Design (from stage 2):

<design>
# Design

## Approach

Add membership special methods to Table and TinyDB. Table dispatches integers and callables to the existing `contains()` method; TinyDB forwards the operation to its default table. Unsupported operands raise `TypeError`.

## Changes

| Path | Symbol | Kind | ACs |
| --- | --- | --- | --- |
| `tinydb/table.py` | `Table.__contains__` | new | AC-1–AC-8 |
| `tinydb/database.py` | `TinyDB.__contains__` | new | AC-1, AC-2, AC-4, AC-7 |

`Table.__contains__(self, item: object) -> bool` checks `isinstance(item, int)` first and calls `self.contains(doc_id=item)`. Otherwise it calls `self.contains(item)` for a callable, or raises `TypeError('Membership requires an integer document ID or a callable query')`. `TinyDB.__contains__(self, item: object) -> bool` returns `item in self.table(self.default_table_name)`.

## Public API and test hooks

Use `item in table` or `item in db`. Integers use ID lookup, callables use query lookup, and other operands raise `TypeError`. Exceptions from a callable propagate. Integer subclasses, including `bool`, use ID lookup; integer dispatch also takes precedence over callable dispatch.

Import `TinyDB` and `Query` from `tinydb` and `MemoryStorage` from `tinydb.storages`. Construct `TinyDB(storage=MemoryStorage)`, insert through `db` or `db.table('people')`, and exercise membership with IDs, query expressions, a lambda, and dictionaries.

## Traceability

- AC-1, AC-2: default-table ID membership uses both new special methods and existing `contains()`.
- AC-3: named-table ID membership uses `Table.__contains__`.
- AC-4: default-table query membership uses both new special methods.
- AC-5, AC-6: named-table query and lambda membership use `Table.__contains__`.
- AC-7: default-table dictionary membership forwards to `Table.__contains__` and raises `TypeError`.
- AC-8: named-table dictionary membership raises `TypeError` in `Table.__contains__`.

## Architecture constraints considered

No imports change (Constraint 1). Existing `contains()` and `get()` retain the whole-storage read and ID conversion paths (Constraints 2 and 5; ADR-1). No writes, query hashes, cache keys, or middleware construction are added (Constraints 3 and 4; ADR-2 and ADR-3).

## Risks

Python considers `bool` an `int`, so it follows the existing ID lookup behavior. Dictionary membership previously fell back to document iteration and equality; rejecting it is an intentional behavior change.

## Changes (machine-checked)

| Path | Symbol | Kind | ACs | Description |
|---|---|---|---|---|
| `tinydb/table.py` | `Table.__contains__` | new | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 | Add def __contains__(self, item: object) -> bool alongside the existing special methods. First check isinstance(item, int) and return self.contains(doc_id=item); otherwise, if callable(item), return self.contains(item). For all other operands, raise TypeError('Membership requires an integer document ID or a callable query'). Integer dispatch takes precedence for objects that are both integers and callable. Do not alter contains(). |
| `tinydb/database.py` | `TinyDB.__contains__` | new | AC-1, AC-2, AC-4, AC-7 | Add def __contains__(self, item: object) -> bool alongside the existing forwarded special methods. Return item in self.table(self.default_table_name), so default-table membership uses the configured table class and propagates its result or exception. |

## Public API / test hooks

- `Table.__contains__(self, item: object) -> bool`: The expression item in table returns table.contains(doc_id=item) for an int, and table.contains(item) for any other callable. It raises TypeError for an operand that is neither an int nor callable. Exceptions raised by a callable propagate. Integer subclasses, including bool, follow the integer branch; an operand that is both an int and callable also follows that branch.
- `TinyDB.__contains__(self, item: object) -> bool`: The expression item in db has the same result or exception as item in db.table(db.default_table_name), including integer ID checks, callable query checks, and TypeError for unsupported operands.

Test hooks:
- Import TinyDB and Query from tinydb and MemoryStorage from tinydb.storages; construct a fresh database with TinyDB(storage=MemoryStorage).
- Use db.insert(...) and db.remove(doc_ids=[1]) for the default table; use db.table('people').insert(...) for a named table.
- Exercise membership with the Python in operator, including a Query expression, a plain lambda, and a dictionary operand.

## Check

design checks passed

</design>

Specification (from stage 1; the acceptance criteria are what the tests check):

<spec>
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
