# Spec — issue #5: pythonic existence checks (`in` operator)

## Summary

Make the `in` operator do the obvious thing on tables and on the database, as specified by the maintainer's answer in the issue thread: an int operand is a document ID, a callable operand is a query, anything else raises `TypeError`. It must work on `TinyDB` (default table) and on named tables. No new methods, no change to `contains()`, performance out of scope.

Issue type: **vague** (clarified by maintainer comment)

## Source excerpts

- **SRC-1 (issue):** "`>>> 1 in db` / `False      # there definitely is a document 1 ??`"
- **SRC-2 (maintainer):** "`doc_id in table` should be `True` if and only if a document with that (int) ID exists, i.e. exactly what `table.contains(doc_id=doc_id)` returns."
- **SRC-3 (maintainer):** "`query in table` (anything callable, e.g. `Query().email == x`) should be `True` if and only if at least one document matches, i.e. exactly `table.contains(query)`."
- **SRC-4 (maintainer):** "Anything else (for example a dict / a document like `{'name': 'alice'} in db`) should raise a `TypeError` instead of silently returning a result."
- **SRC-5 (maintainer):** "It has to work on both `TinyDB` (the default table) and on named tables … magic methods aren't forwarded by `TinyDB.__getattr__`"
- **SRC-6 (maintainer):** "No new methods, no changes to `contains()` itself, and the speed of large tables is out of scope"

## Requirements

| ID | Requirement | Provenance | Sources |
|---|---|---|---|
| REQ-1 | `doc_id in t` ⇔ `t.contains(doc_id=doc_id)` for int operands. | CONFIRMED | SRC-1, SRC-2 |
| REQ-2 | `query in t` ⇔ `t.contains(query)` for callable operands. | CONFIRMED | SRC-3 |
| REQ-3 | Any other operand raises `TypeError`. | CONFIRMED | SRC-4 |
| REQ-4 | REQ-1..3 hold for `TinyDB` and for named tables. | CONFIRMED | SRC-5 |
| REQ-5 | No new public methods; `contains()` unchanged. | CONFIRMED | SRC-6 |

## Acceptance criteria

- **AC-1** (REQ-1, REQ-4) — *Given* a database with documents 1 and 2 — *when* `n in db` is evaluated for existing and non-existing ids, and again after `db.remove(doc_ids=[1])` — *then* the result equals `db.contains(doc_id=n)` in every case (`1 in db` is `True` before and `False` after the removal). *Observable:* boolean result.
- **AC-2** (REQ-2, REQ-4) — *Given* the same database — *when* `q in db` is evaluated for matching and non-matching queries — *then* the result equals `db.contains(q)`. *Observable:* boolean result.
- **AC-3** (REQ-3) — *Given* the same database — *when* `{'name': 'alice'} in db` is evaluated — *then* `TypeError` is raised. *Observable:* exception.
- **AC-4** (REQ-4) — *Given* a named table `people` with one document — *when* id and query membership are evaluated on the table — *then* results follow AC-1/AC-2 for that table only. *Observable:* boolean result.

## Open questions

- **Q-1** (non-blocking): `bool` is a subclass of `int` (`True in db`). *Default:* treated as an int id, like `contains(doc_id=True)`.

## Out of scope

- Speeding up existence checks on large tables (needs indexes).
- New methods (`exists()`, etc.) or changes to `contains()`.

## Injection findings

None.
