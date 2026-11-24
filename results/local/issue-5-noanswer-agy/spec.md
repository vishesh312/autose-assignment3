# Spec: issue #5: checking if something is in the db is really clunky

# Specification: TinyDB Issue #5

**Status**: NOT READY (blocked by Q-1)  
**Issue Type**: vague  

## Summary
Adds membership testing support using the Python `in` operator (`__contains__`) for document IDs on `TinyDB` and `Table` instances. Currently, evaluating `doc_id in db` falls back to iterating all documents and comparing equality against `doc_id`, returning `False` and incurring significant performance overhead on large tables. This change specifies document ID existence checks while raising an open question regarding how query-based existence checks should be structured in the public API.

## Source Excerpts
| ID | Quote |
|---|---|
| `SRC-1` | "checking if something is in the db is really clunky" |
| `SRC-2` | "Checking whether a record exists in TinyDB is just awkward compared to everything else in the library which is super pythonic." |
| `SRC-3` | "Right now I end up writing stuff like\n\n```python\nif db.search(User.email == email):\n    ...\nif len(db.search(User.email == email)) > 0:\n    ...\n```\n\nor digging through the docs for the right method and the right keyword argument every time." |
| `SRC-4` | "And when I tried the obvious thing it just quietly says no:\n\n```python\n>>> 1 in db\nFalse      # there definitely is a document 1 ??\n```\n\nwhich cost me a while of debugging." |
| `SRC-5` | "It's also slow on my bigger file (~20k docs) when I just want a yes/no." |
| `SRC-6` | "Can existence checks be made nicer / more pythonic? Not sure what the best API is, you know the codebase better, but right now it feels like a footgun." |

## Requirements
- **REQ-1**: The `Table` class shall support the membership test operator `in` (`__contains__`) for document IDs, returning `True` if a document with the specified document ID exists in the table and `False` otherwise.
  - *Provenance*: DERIVED
  - *Trace*: `SRC-4`
  - *Status*: Ready
- **REQ-2**: The `TinyDB` class shall delegate the membership test operator `in` (`__contains__`) to its default table, returning `True` if a document with the specified document ID exists in the default table and `False` otherwise.
  - *Provenance*: STATED
  - *Trace*: `SRC-4`
  - *Status*: Ready

## Acceptance Criteria
- **AC-1** (re: `REQ-2`)
  - **Given**: A TinyDB instance using MemoryStorage containing one document with document ID 1 in the default table.
  - **When**: The expression `1 in db` is evaluated.
  - **Then**: The membership test evaluates to `True`.
  - **Observable**: `(1 in db) is True`
- **AC-2** (re: `REQ-2`)
  - **Given**: A TinyDB instance using MemoryStorage containing one document with document ID 1 in the default table.
  - **When**: The expression `999 in db` is evaluated.
  - **Then**: The membership test evaluates to `False`.
  - **Observable**: `(999 in db) is False`
- **AC-3** (re: `REQ-1`)
  - **Given**: A Table instance `test_table` in a TinyDB database using MemoryStorage containing one document with document ID 1.
  - **When**: The expression `1 in table` is evaluated on `test_table`.
  - **Then**: The membership test evaluates to `True`.
  - **Observable**: `(1 in table) is True`
- **AC-4** (re: `REQ-1`)
  - **Given**: A Table instance `test_table` in a TinyDB database using MemoryStorage containing one document with document ID 1.
  - **When**: The expression `999 in table` is evaluated on `test_table`.
  - **Then**: The membership test evaluates to `False`.
  - **Observable**: `(999 in table) is False`
- **AC-5** (re: `REQ-1`)
  - **Given**: An empty Table instance `test_table` in a TinyDB database using MemoryStorage with no documents.
  - **When**: The expression `1 in table` is evaluated on `test_table`.
  - **Then**: The membership test evaluates to `False`.
  - **Observable**: `(1 in table) is False`

## Open Questions
- **Q-1** (Blocking)
  - **Question**: In "Can existence checks be made nicer / more pythonic? Not sure what the best API is", what API should TinyDB provide for checking document existence beyond document ID membership?
  - **Why It Matters**: INTENT: The phrase "nicer / more pythonic" and admission "Not sure what the best API is" express a desire for an improved API without specifying it. Two plausible interpretations lead to different acceptance tests: supporting queries via the `in` operator (e.g. `(where('email') == email) in db`) requires acceptance tests asserting boolean results for Query conditions in `__contains__`, whereas restricting `in` to document IDs or retaining `db.contains(cond)` for queries means `query in db` would either raise a TypeError or not be tested.
  - **Options**:
    1. Implement `__contains__` on `Table` and `TinyDB` to support both document IDs (e.g., `1 in db`) and Query conditions (e.g., `(where('x') == 1) in db`).
    2. Implement `__contains__` on `Table` and `TinyDB` to support only document IDs (e.g., `1 in db`), leaving query existence checks to the existing `db.contains(cond)` method.
    3. Make `Table.contains` and `TinyDB.contains` accept a document ID as the first positional argument (e.g., `db.contains(1)` instead of requiring keyword argument `doc_id=1`).
  - **Default If Unanswered**: null
- **Q-2** (Non-blocking)
  - **Question**: The issue states: "It's also slow on my bigger file (~20k docs) when I just want a yes/no." Are specific execution time thresholds or benchmark constraints required for existence checks?
  - **Why It Matters**: INTENT: "slow" is a vague performance descriptor without a quantitative target. In unit testing, O(1) dictionary key lookup avoids full-table iteration and satisfies the functional requirement without imposing wall-clock latency assertions.
  - **Options**:
    1. Rely on constant-time O(1) document ID lookup in table storage without explicit timing assertions in acceptance tests.
    2. Specify a quantitative latency limit asserted via automated performance tests.
  - **Default If Unanswered**: "Rely on constant-time O(1) document ID lookup in table storage without explicit timing assertions in acceptance tests."

## Assumptions
- Document IDs tested via `in` are integers, matching TinyDB's `DocumentIdClass` / integer ID convention.
- Magic methods on `TinyDB` forward directly to the default table instance (`_default`), consistent with `__len__` and `__iter__`.

## Out of Scope
- Supporting `QueryLike` conditions with the `in` operator (blocked by open question Q-1).
- Arbitrary document dictionary equality checks via the `in` operator (e.g., `{'key': 'value'} in db`).
- Wall-clock performance benchmarks or quantitative latency guarantees in automated acceptance tests.
- Modifying, renaming, or deprecating existing `contains()` methods.

## Injection Findings
None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A TinyDB instance using MemoryStorage containing one document with document ID 1 in the default table. | The expression '1 in db' is evaluated. | The membership test evaluates to True. | (1 in db) is True | - |
| AC-2 | A TinyDB instance using MemoryStorage containing one document with document ID 1 in the default table. | The expression '999 in db' is evaluated. | The membership test evaluates to False. | (999 in db) is False | - |
| AC-3 | A Table instance 'test_table' in a TinyDB database using MemoryStorage containing one document with document ID 1. | The expression '1 in table' is evaluated on 'test_table'. | The membership test evaluates to True. | (1 in table) is True | - |
| AC-4 | A Table instance 'test_table' in a TinyDB database using MemoryStorage containing one document with document ID 1. | The expression '999 in table' is evaluated on 'test_table'. | The membership test evaluates to False. | (999 in table) is False | - |
| AC-5 | An empty Table instance 'test_table' in a TinyDB database using MemoryStorage with no documents. | The expression '1 in table' is evaluated on 'test_table'. | The membership test evaluates to False. | (1 in table) is False | - |

## Open questions

- **Q-1** (blocking): In 'Can existence checks be made nicer / more pythonic? Not sure what the best API is', what API should TinyDB provide for checking document existence beyond document ID membership?
- **Q-2**: The issue states: 'It's also slow on my bigger file (~20k docs) when I just want a yes/no.' Are specific execution time thresholds or benchmark constraints required for existence checks?


## Stop reason

The issue has blocking open questions; they were posted on the issue.
