Write the tests for tinydb issue #4. The only file you may create or edit is `tests/test_autose_issue_4.py`.

Acceptance criteria (from the spec; derive every expected value from these):

<acceptance_criteria>
- **AC-1** Given A TinyDB using MemoryStorage whose default table contains, in insertion order, {'status': 'open', 'n': 1}, {'status': 'closed', 'n': 2}, {'status': 'open', 'n': 3}, and {'status': 'open', 'n': 4}; q is Query().status == 'open'.; when Call db.search(q, limit=2).; then The first two matching documents are returned in insertion order.. Observable: The returned list equals [{'status': 'open', 'n': 1}, {'status': 'open', 'n': 3}].
- **AC-2** Given A TinyDB using MemoryStorage whose named table 'x' contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0.; when Call db.table('x').search(q, limit=5).; then Both matching documents are returned in insertion order.. Observable: The returned list equals [{'n': 1}, {'n': 2}].
- **AC-3** Given A TinyDB using MemoryStorage whose default table contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0.; when Call db.search(q, limit=None).; then Both matching documents are returned in insertion order.. Observable: The returned list equals [{'n': 1}, {'n': 2}].
- **AC-4** Given A TinyDB using MemoryStorage whose default table contains {'n': 1}; q is Query().n > 0.; when Call db.search(q, limit=0).; then The search returns no documents.. Observable: The returned value equals [].
- **AC-5** Given A TinyDB using MemoryStorage whose default table contains {'n': 1}; q is Query().n > 0.; when Call db.search(q, limit=-1).; then The search rejects the negative limit.. Observable: The call raises ValueError.
- **AC-6** Given A TinyDB using MemoryStorage with the default query cache enabled; its default table contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0; db.search(q, limit=1) has already been called.; when Call db.search(q).; then The unlimited search returns both matching documents in insertion order.. Observable: The returned list equals [{'n': 1}, {'n': 2}].
- **AC-7** Given A TinyDB using MemoryStorage with the default query cache enabled; its default table contains, in insertion order, {'n': 1} and {'n': 2}; q is Query().n > 0; db.search(q) has already been called.; when Call db.search(q, limit=1).; then The limited search returns only the first matching document.. Observable: The returned list equals [{'n': 1}].
</acceptance_criteria>

Public API / test hooks (from the design):

<public_api>
## Public API / test hooks

- `Table.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`: Returns matching Document objects in the existing search order. None or an omitted limit returns all matches; a positive integer returns at most that many, starting with the first match; zero returns an empty list; a negative integer raises ValueError. Each call applies its own limit regardless of prior searches for the same condition. The argument may be passed positionally or by keyword.
- `TinyDB.search(self, cond: QueryLike, limit: Optional[int] = None) -> list[Document]`: Forwarded dynamically to the default table's Table.search, with the same return values, limit behavior, and ValueError for negative integers.

Test hooks:
- Import TinyDB and Query from tinydb and MemoryStorage from tinydb.storages; construct an empty database with TinyDB(storage=MemoryStorage).
- Use db.insert or db.insert_multiple for default-table documents and db.table('x').insert or insert_multiple for named-table documents. Document is a dict subclass, so returned lists can be compared directly with lists of dicts.
- The default query cache is enabled; exercise both limited-then-unlimited and unlimited-then-limited searches with the same query. Also exercise omitted and explicit None limits, zero, and a negative limit.
- TinyDB.search is provided by dynamic forwarding to the default table; named tables expose Table.search directly.
</public_api>

Contested tests (empty unless the Developer contested a test; each entry has the test id and the Developer's reason):

<contested_tests>

</contested_tests>

Reviewer findings about your tests (address them; revise the test file accordingly). This is `none` unless the independent reviewer sent the PR back to the testing stage:

<review_findings>
none
</review_findings>

Write at least one test per criterion named `test_ac<N>_<slug>`, run `python -m pytest tests/test_autose_issue_4.py -q` and `python -m pytest -q`, then return the `test_map.json` object as your final answer.
