"""Hidden acceptance tests for issue 1: update/remove ignore string doc_ids.

get(doc_id='1') finds the document, so update(..., doc_ids=['1']) and
remove(doc_ids=['1']) must act on the same document instead of silently
doing nothing.
"""
from tinydb import TinyDB
from tinydb.storages import MemoryStorage


def _db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'a', 'n': 1})
    db.insert({'name': 'b', 'n': 2})
    db.insert({'name': 'c', 'n': 3})
    return db


def test_update_accepts_string_doc_ids():
    db = _db()
    assert db.get(doc_id='2') is not None  # reads already accept '2'

    result = db.update({'n': 20}, doc_ids=['2'])

    assert result == [2]
    assert db.get(doc_id=2)['n'] == 20
    # other documents untouched
    assert db.get(doc_id=1)['n'] == 1
    assert db.get(doc_id=3)['n'] == 3


def test_remove_accepts_string_doc_ids():
    db = _db()

    result = db.remove(doc_ids=['1', '3'])

    assert sorted(result) == [1, 3]
    assert len(db) == 1
    assert db.get(doc_id=1) is None
    assert db.get(doc_id=3) is None
    assert db.get(doc_id=2)['name'] == 'b'


def test_string_ids_on_named_table_and_with_file_storage(tmp_path):
    path = tmp_path / 'db.json'
    with TinyDB(path) as db:
        table = db.table('things')
        table.insert_multiple([{'v': 1}, {'v': 2}])
        assert table.update({'v': 99}, doc_ids=['2']) == [2]
        assert table.remove(doc_ids=['1']) == [1]

    with TinyDB(path) as db:
        table = db.table('things')
        assert [(d.doc_id, d['v']) for d in table.all()] == [(2, 99)]


def test_int_ids_and_missing_string_ids_still_behave():
    db = _db()
    # int IDs keep working
    assert db.update({'n': 10}, doc_ids=[1]) == [1]
    # IDs that do not exist are skipped, not an error (see upstream #591)
    assert db.update({'n': 0}, doc_ids=['99']) == []
    assert db.remove(doc_ids=['99']) == []
    assert len(db) == 3
