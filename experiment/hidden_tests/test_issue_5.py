"""Hidden acceptance tests for issue 5 (vague: "checking if something is in
the db is clunky"), as pinned down by the maintainer's answer:

* ``doc_id in table`` / ``doc_id in db`` -> True iff a document with that
  int ID exists;
* ``query in table`` / ``query in db``   -> True iff any document matches;
* any other operand (e.g. a dict)        -> TypeError, not a silent False.
"""
import pytest

from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage


def _db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice', 'age': 30})
    db.insert({'name': 'bob', 'age': 25})
    return db


def test_doc_id_membership_on_db_and_table():
    db = _db()
    assert 1 in db
    assert 2 in db
    assert 3 not in db

    db.remove(doc_ids=[1])
    assert 1 not in db

    table = db.table('people')
    table.insert({'name': 'carol'})
    assert 1 in table
    assert 2 not in table


def test_query_membership_on_db_and_table():
    db = _db()
    assert (Query().name == 'bob') in db
    assert (where('age') > 100) not in db

    table = db.table('people')
    table.insert({'name': 'carol'})
    assert (Query().name == 'carol') in table
    assert (Query().name == 'bob') not in table


def test_membership_agrees_with_contains():
    db = _db()
    for doc_id in (1, 2, 3, 99):
        assert (doc_id in db) == db.contains(doc_id=doc_id)
    for q in (Query().age == 25, Query().age == 26):
        assert (q in db) == db.contains(q)


def test_unsupported_operand_raises_type_error():
    db = _db()
    with pytest.raises(TypeError):
        {'name': 'alice', 'age': 30} in db  # noqa: B015
    with pytest.raises(TypeError):
        {'name': 'alice'} in db.table('_default')  # noqa: B015
