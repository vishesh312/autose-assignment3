Write the tests for tinydb issue #5. The only file you may create or edit is `tests/test_autose_issue_5.py`.

Acceptance criteria (from the spec; derive every expected value from these):

<acceptance_criteria>
- **AC-1** Given A new TinyDB using MemoryStorage whose default table has just inserted {'name': 'alice'} as document ID 1.; when Evaluate 1 in db.; then The membership check reports that document ID 1 exists.. Observable: The expression returns True.
- **AC-2** Given A new TinyDB using MemoryStorage whose default table inserted {'name': 'alice'} as document ID 1 and then called db.remove(doc_ids=[1]).; when Evaluate 1 in db.; then The membership check reports that document ID 1 no longer exists.. Observable: The expression returns False.
- **AC-3** Given A new TinyDB using MemoryStorage with a named table db.table('people') that has inserted {'name': 'alice'} as document ID 1.; when Evaluate 1 in db.table('people').; then The membership check reports that document ID 1 exists in the named table.. Observable: The expression returns True.
- **AC-4** Given A new TinyDB using MemoryStorage whose default table contains {'email': 'alice@example.com'}.; when Evaluate (Query().email == 'alice@example.com') in db.; then The membership check reports a matching document.. Observable: The expression returns True.
- **AC-5** Given A new TinyDB using MemoryStorage with a named table db.table('people') containing {'email': 'alice@example.com'}.; when Evaluate (Query().email == 'bob@example.com') in db.table('people').; then The membership check reports that no document matches.. Observable: The expression returns False.
- **AC-6** Given A new TinyDB using MemoryStorage with a named table db.table('people') containing {'name': 'alice'}.; when Evaluate (lambda doc: doc['name'] == 'alice') in db.table('people').; then The membership check evaluates the callable against the table's documents and reports a match.. Observable: The expression returns True.
- **AC-7** Given A new TinyDB using MemoryStorage whose default table contains {'name': 'alice'}.; when Evaluate {'name': 'alice'} in db.; then The membership check rejects the dictionary operand.. Observable: The expression raises TypeError.
- **AC-8** Given A new TinyDB using MemoryStorage with a named table db.table('people') containing {'name': 'alice'}.; when Evaluate {'name': 'alice'} in db.table('people').; then The membership check rejects the dictionary operand.. Observable: The expression raises TypeError.
</acceptance_criteria>

Public API / test hooks (from the design):

<public_api>
## Public API / test hooks

- `Table.__contains__(self, item: object) -> bool`: The expression item in table returns table.contains(doc_id=item) for an int, and table.contains(item) for any other callable. It raises TypeError for an operand that is neither an int nor callable. Exceptions raised by a callable propagate. Integer subclasses, including bool, follow the integer branch; an operand that is both an int and callable also follows that branch.
- `TinyDB.__contains__(self, item: object) -> bool`: The expression item in db has the same result or exception as item in db.table(db.default_table_name), including integer ID checks, callable query checks, and TypeError for unsupported operands.

Test hooks:
- Import TinyDB and Query from tinydb and MemoryStorage from tinydb.storages; construct a fresh database with TinyDB(storage=MemoryStorage).
- Use db.insert(...) and db.remove(doc_ids=[1]) for the default table; use db.table('people').insert(...) for a named table.
- Exercise membership with the Python in operator, including a Query expression, a plain lambda, and a dictionary operand.
</public_api>

Contested tests (empty unless the Developer contested a test; each entry has the test id and the Developer's reason):

<contested_tests>

</contested_tests>

Reviewer findings about your tests (address them; revise the test file accordingly). This is `none` unless the independent reviewer sent the PR back to the testing stage:

<review_findings>
none
</review_findings>

Write at least one test per criterion named `test_ac<N>_<slug>`, run `python -m pytest tests/test_autose_issue_5.py -q` and `python -m pytest -q`, then return the `test_map.json` object as your final answer.
