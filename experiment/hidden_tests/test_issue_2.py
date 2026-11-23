"""Hidden acceptance tests for issue 2: fragment() on different fields
shares one query-cache entry, so search() returns stale results.
"""
from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage


def _db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}})
    db.insert({'home': {'city': 'Rome'}, 'work': {'city': 'Paris'}})
    return db


def test_search_fragment_on_two_fields_returns_own_results():
    db = _db()
    frag = {'city': 'Paris'}

    home = db.search(Query().home.fragment(frag))
    work = db.search(Query().work.fragment(frag))

    assert [d.doc_id for d in home] == [1]
    assert [d.doc_id for d in work] == [2]
    # and again, now that both are cached
    assert [d.doc_id for d in db.search(where('home').fragment(frag))] == [1]
    assert [d.doc_id for d in db.search(where('work').fragment(frag))] == [2]


def test_count_and_get_with_fragment_on_other_field():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}})
    frag = {'city': 'Paris'}

    assert db.count(Query().home.fragment(frag)) == 1
    assert db.count(Query().work.fragment(frag)) == 0
    assert db.get(Query().work.fragment(frag)) is None


def test_fragment_queries_on_different_paths_are_not_equal():
    frag = {'a': 1}
    assert Query().x.fragment(frag) != Query().y.fragment(frag)
    assert Query().x.fragment(frag) != Query().fragment(frag)
    # same path + same fragment must still be equal/hash-equal (cacheable)
    assert Query().x.fragment(frag) == Query().x.fragment({'a': 1})
    assert hash(Query().x.fragment(frag)) == hash(Query().x.fragment(frag))
