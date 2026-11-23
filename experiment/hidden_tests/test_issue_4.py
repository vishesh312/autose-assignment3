"""Hidden acceptance tests for issue 4: ``search(cond, limit=N)``."""
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def _db():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple({'i': i, 'even': i % 2 == 0} for i in range(10))
    return db


def test_limit_returns_first_n_matches_in_insertion_order():
    db = _db()
    q = Query().even == True  # noqa: E712

    result = db.search(q, limit=2)

    assert [d['i'] for d in result] == [0, 2]
    assert [d.doc_id for d in result] == [1, 3]


def test_limit_does_not_poison_the_query_cache():
    db = _db()
    q = Query().i >= 3

    assert len(db.search(q, limit=1)) == 1
    assert len(db.search(q)) == 7          # full result after a limited one
    assert len(db.search(q, limit=3)) == 3  # limited result after a full one
    assert len(db.search(q)) == 7
    assert db.count(q) == 7


def test_limit_larger_than_matches_or_none_returns_everything():
    db = _db()
    q = Query().i < 4

    assert [d['i'] for d in db.search(q, limit=100)] == [0, 1, 2, 3]
    assert [d['i'] for d in db.search(q, limit=None)] == [0, 1, 2, 3]
    assert [d['i'] for d in db.search(q)] == [0, 1, 2, 3]


def test_limit_on_named_table():
    db = _db()
    table = db.table('other')
    table.insert_multiple({'v': v} for v in 'abcde')

    result = table.search(Query().v.exists(), limit=3)

    assert [d['v'] for d in result] == ['a', 'b', 'c']
