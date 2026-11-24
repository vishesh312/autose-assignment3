# Spec: issue #5: Support membership test operator (`in`) for document IDs and queries on tables and databases

# Specification: Support Membership Test Operator (`in`) for TinyDB and Table

**Status:** READY (4 of 4 requirements Ready)  
**Mode:** batch  
**Issue:** #5  
**Issue Type:** feature  

## Summary
Add support for the Python membership test operator (`in`) on both `Table` and `TinyDB` instances. Evaluating `doc_id in table` checks if a document with that integer ID exists (matching `table.contains(doc_id=doc_id)`), evaluating `query in table` checks if any document matches the callable query (matching `table.contains(query)`), and evaluating any other operand type raises a `TypeError`. This eliminates the misleading footgun where `1 in db` quietly returned `False` by falling back to document iteration.

## Source Excerpts
- **SRC-1**: "checking if something is in the db is really clunky" (Issue Title)
- **SRC-2**: ">>> 1 in db\nFalse      # there definitely is a document 1 ??" (Issue Body)
- **SRC-3**: "It's also slow on my bigger file (~20k docs) when I just want a yes/no." (Issue Body)
- **SRC-4**: "Can existence checks be made nicer / more pythonic? Not sure what the best API is, you know the codebase better, but right now it feels like a footgun." (Issue Body)
- **SRC-5**: "Agreed that `1 in db` quietly returning `False` is a footgun (it currently falls back to iterating the documents and comparing each document to `1`). Let's keep the scope small and just make the `in` operator do the obvious thing." (Maintainer Comment)
- **SRC-6**: "1. **Doc IDs:** `doc_id in table` should be `True` if and only if a document with that (int) ID exists, i.e. exactly what `table.contains(doc_id=doc_id)` returns. So `1 in db` is `True` after the first insert and `False` again after `db.remove(doc_ids=[1])`." (Maintainer Comment)
- **SRC-7**: "2. **Queries:** `query in table` (anything callable, e.g. `Query().email == x`) should be `True` if and only if at least one document matches, i.e. exactly `table.contains(query)`." (Maintainer Comment)
- **SRC-8**: "3. **Anything else** (for example a dict / a document like `{'name': 'alice'} in db`) should raise a `TypeError` instead of silently returning a result. We don't want to support \"is this exact document in the table\" semantics." (Maintainer Comment)
- **SRC-9**: "4. It has to work on both `TinyDB` (the default table) and on named tables from `db.table('...')`. Note that magic methods aren't forwarded by `TinyDB.__getattr__`, so the database needs its own forwarding like `__len__`/`__iter__` already have." (Maintainer Comment)
- **SRC-10**: "No new methods, no changes to `contains()` itself, and the speed of large tables is out of scope for this issue (that would need indexes, which TinyDB doesn't have). Please add tests for the four points above." (Maintainer Comment)

## Requirements
- **REQ-1** (Doc ID Membership): When an integer document ID is tested for membership using the `in` operator (`doc_id in table`), the `Table` instance shall return `True` if a document with that integer ID exists in the table, and `False` otherwise, equivalent to `table.contains(doc_id=doc_id)`.
  - Provenance: CONFIRMED
  - Trace: `SRC-2`, `SRC-5`, `SRC-6`
  - Acceptance Criteria: `AC-1`, `AC-2`
  - Status: Ready
- **REQ-2** (Query Membership): When a callable query is tested for membership using the `in` operator (`query in table`), the `Table` instance shall return `True` if at least one document in the table matches the query, and `False` otherwise, equivalent to `table.contains(query)`.
  - Provenance: CONFIRMED
  - Trace: `SRC-7`
  - Acceptance Criteria: `AC-3`, `AC-4`
  - Status: Ready
- **REQ-3** (Unsupported Operand Type): If an operand that is neither an integer document ID nor a callable query is tested for membership using the `in` operator (`item in table`), the `Table` instance shall raise a `TypeError`.
  - Provenance: CONFIRMED
  - Trace: `SRC-8`
  - Acceptance Criteria: `AC-5`
  - Status: Ready
- **REQ-4** (TinyDB Forwarding): When a membership test using the `in` operator is evaluated on a `TinyDB` database instance (`item in db`), the database shall forward the membership test to its default table instance.
  - Provenance: CONFIRMED
  - Trace: `SRC-9`
  - Acceptance Criteria: `AC-6`
  - Status: Ready

## Acceptance Criteria
- **AC-1** (Parent: REQ-1)
  - Given: A TinyDB instance initialized with MemoryStorage where a document `{'name': 'alice'}` has been inserted with document ID 1.
  - When: `1 in db` is evaluated.
  - Then: The expression evaluates to True.
  - Observable: `1 in db == True`
- **AC-2** (Parent: REQ-1)
  - Given: A TinyDB instance initialized with MemoryStorage where a document with document ID 1 was inserted and subsequently removed via `db.remove(doc_ids=[1])`.
  - When: `1 in db` is evaluated.
  - Then: The expression evaluates to False.
  - Observable: `1 in db == False`
- **AC-3** (Parent: REQ-2)
  - Given: A TinyDB instance initialized with MemoryStorage containing a document `{'int': 1, 'char': 'a'}` and a query `where('int') == 1`.
  - When: `(where('int') == 1) in db` is evaluated.
  - Then: The expression evaluates to True.
  - Observable: `(where('int') == 1) in db == True`
- **AC-4** (Parent: REQ-2)
  - Given: A TinyDB instance initialized with MemoryStorage containing a document `{'int': 1, 'char': 'a'}` and a query `where('int') == 2`.
  - When: `(where('int') == 2) in db` is evaluated.
  - Then: The expression evaluates to False.
  - Observable: `(where('int') == 2) in db == False`
- **AC-5** (Parent: REQ-3)
  - Given: A TinyDB instance initialized with MemoryStorage containing a document `{'name': 'alice'}`.
  - When: `{'name': 'alice'} in db` is evaluated.
  - Then: A TypeError is raised.
  - Observable: Evaluating `{'name': 'alice'} in db` raises TypeError
- **AC-6** (Parent: REQ-4)
  - Given: A TinyDB instance initialized with MemoryStorage where a named table `table = db.table('users')` has a document `{'name': 'bob'}` inserted with document ID 1, while the default table remains empty.
  - When: `1 in table` is evaluated.
  - Then: The expression evaluates to True on the named table instance.
  - Observable: `1 in db.table('users') == True`

## Open Questions
None. All requirements, behavioral semantics, and scope boundaries were confirmed by the maintainer.

## Assumptions
None.

## Out of Scope
- Performance optimizations or indexing mechanisms for large tables (e.g. ~20k documents) to speed up membership testing.
- Membership testing for exact dictionary or document values (e.g. `{'name': 'alice'} in db`), which shall raise a TypeError instead.
- Adding new existence check methods to `Table` or `TinyDB`.
- Modifying the existing `contains()` method implementation or signature.

## Injection Findings
None.

## Acceptance criteria (machine-checked)

| AC | Given | When | Then | Observable | Judge |
|---|---|---|---|---|---|
| AC-1 | A TinyDB instance initialized with MemoryStorage where a document {'name': 'alice'} has been inserted with document ID 1. | 1 in db is evaluated. | The expression evaluates to True. | 1 in db == True | testable |
| AC-2 | A TinyDB instance initialized with MemoryStorage where a document with document ID 1 was inserted and subsequently removed via db.remove(doc_ids=[1]). | 1 in db is evaluated. | The expression evaluates to False. | 1 in db == False | testable |
| AC-3 | A TinyDB instance initialized with MemoryStorage containing a document {'int': 1, 'char': 'a'} and a query where('int') == 1. | (where('int') == 1) in db is evaluated. | The expression evaluates to True. | (where('int') == 1) in db == True | testable |
| AC-4 | A TinyDB instance initialized with MemoryStorage containing a document {'int': 1, 'char': 'a'} and a query where('int') == 2. | (where('int') == 2) in db is evaluated. | The expression evaluates to False. | (where('int') == 2) in db == False | testable |
| AC-5 | A TinyDB instance initialized with MemoryStorage containing a document {'name': 'alice'}. | {'name': 'alice'} in db is evaluated. | A TypeError is raised. | Evaluating {'name': 'alice'} in db raises TypeError | testable |
| AC-6 | A TinyDB instance initialized with MemoryStorage where a named table table = db.table('users') has a document {'name': 'bob'} inserted with document ID 1, while the default table remains empty. | 1 in table is evaluated. | The expression evaluates to True on the named table instance. | 1 in db.table('users') == True | testable |

## Check

all criteria testable
