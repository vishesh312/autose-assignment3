# Spec: issue #5: Checking if something is in the db is really clunky

# Issue 5: Existence checks

**Status: NOT READY — Q-1 and Q-2 are blocking.**

The reporter wants a more convenient way to check whether a document exists, including checks by query and the reported document-ID example. The intended API and performance goal need clarification. The existing `db.contains` API already provides query and document-ID checks; the criteria below establish the clear query behavior but do not determine the requested API change.

## Source excerpts

- SRC-1: “Checking whether a record exists in TinyDB is just awkward”
- SRC-2: `if db.search(User.email == email):`
- SRC-3: `>>> 1 in db` / `False      # there definitely is a document 1 ??`
- SRC-4: “It's also slow on my bigger file (~20k docs) when I just want a yes/no.”
- SRC-5: “Can existence checks be made nicer / more pythonic? Not sure what the best API is”

## Requirement

- **REQ-1 — STATED (SRC-2, SRC-4):** TinyDB shall allow a caller to obtain a boolean indicating whether a document matches a query.

## Acceptance criteria

- **AC-1 (REQ-1):** Given a TinyDB using MemoryStorage whose default table contains `{'email': 'a@example.com'}` and `{'email': 'b@example.com'}`, when the caller evaluates `db.contains(where('email') == 'a@example.com')`, then the return value is the boolean `True`.
- **AC-2 (REQ-1):** Given a TinyDB using MemoryStorage whose default table contains `{'email': 'a@example.com'}`, when the caller evaluates `db.contains(where('email') == 'missing@example.com')`, then the return value is the boolean `False`.

These criteria cover existing behavior; no criterion for a changed membership result can be specified until Q-1 is answered.

## Open questions

- **Q-1 — blocking:** What should “nicer / more pythonic” existence checks provide, including for `1 in db`? Options: make membership check document IDs and retain query checks through `db.contains`; use membership for IDs and queries; keep membership behavior and improve `db.contains` or its documentation; or introduce another explicit API, specifying its name and arguments. INTENT: the choice changes the calls and expected results. Default: none.
- **Q-2 — blocking:** What measurable behavior should address “It's also slow on my bigger file (~20k docs)”? Options: stop query evaluation after the first match; meet a specified time target for a specified workload and environment; or add no performance requirement. INTENT: these choices require different tests. Default: none.

## Assumptions

None.

## Out of scope

A specific implementation or new dependency. The reported Python and Windows versions are environment context, not an identified platform requirement.

## Injection findings

None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A TinyDB using MemoryStorage whose default table contains {'email': 'a@example.com'} and {'email': 'b@example.com'}. | The caller evaluates db.contains(where('email') == 'a@example.com'). | The existence check reports that a matching document exists. | The return value is the boolean True. | - |
| AC-2 | A TinyDB using MemoryStorage whose default table contains {'email': 'a@example.com'}. | The caller evaluates db.contains(where('email') == 'missing@example.com'). | The existence check reports that no matching document exists. | The return value is the boolean False. | - |

## Open questions

- **Q-1** (blocking): What should “nicer / more pythonic” existence checks provide, including for the reported `1 in db` example?
- **Q-2** (blocking): What measurable behavior should address “It's also slow on my bigger file (~20k docs)”?


## Stop reason

The issue has blocking open questions; they were posted on the issue.
