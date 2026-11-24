from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_limit_returns_first_matching_docs_in_order():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})
    db.insert({'name': 'doc3', 'val': 1})

    results = db.search(where('val') == 1, limit=2)

    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1},
    ]
    assert results[0].doc_id < results[1].doc_id


def test_ac1_limit_interspersed_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'other', 'val': 2})
    db.insert({'name': 'doc2', 'val': 1})
    db.insert({'name': 'doc3', 'val': 1})

    results = db.search(where('val') == 1, limit=2)

    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1},
    ]


def test_ac2_limit_exceeding_total_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})

    results = db.search(where('val') == 1, limit=5)

    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1},
    ]


def test_ac2_limit_equal_total_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})

    results = db.search(where('val') == 1, limit=2)

    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1},
    ]


def test_ac3_limit_zero_returns_empty_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})

    results = db.search(where('val') == 1, limit=0)

    assert results == []
    assert len(results) == 0


def test_ac3_limit_zero_on_empty_table():
    db = TinyDB(storage=MemoryStorage)

    results = db.search(where('val') == 1, limit=0)

    assert results == []
    assert len(results) == 0


def test_ac4_limit_none_and_omitted_return_all_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 10})
    db.insert({'name': 'doc2', 'val': 10})
    db.insert({'name': 'doc3', 'val': 20})

    res_none = db.search(where('val') == 10, limit=None)
    res_default = db.search(where('val') == 10)

    assert res_none == res_default
    assert len(res_none) == 2
    assert res_none == [
        {'name': 'doc1', 'val': 10},
        {'name': 'doc2', 'val': 10},
    ]


def test_ac5_named_table_search_with_limit():
    db = TinyDB(storage=MemoryStorage)
    tasks = db.table('tasks')
    tasks.insert({'task': 't1', 'status': 'open'})
    tasks.insert({'task': 't2', 'status': 'open'})
    tasks.insert({'task': 't3', 'status': 'open'})

    results = tasks.search(where('status') == 'open', limit=1)

    assert len(results) == 1
    assert results == [{'task': 't1', 'status': 'open'}]


def test_ac6_query_cache_isolation_and_no_leakage():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 1})
    db.insert({'val': 1})
    db.insert({'val': 1})

    res1 = db.search(where('val') == 1, limit=1)
    res2 = db.search(where('val') == 1)
    res3 = db.search(where('val') == 1, limit=1)

    assert len(res1) == 1
    assert len(res2) == 3
    assert len(res3) == 1


def test_ac6_cache_unlimited_then_limited_then_unlimited():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 1})
    db.insert({'val': 1})
    db.insert({'val': 1})

    res1 = db.search(where('val') == 1)
    res2 = db.search(where('val') == 1, limit=2)
    res3 = db.search(where('val') == 1)

    assert len(res1) == 3
    assert len(res2) == 2
    assert len(res3) == 3


def test_ac6_returned_lists_are_fresh_copies():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 1})

    res = db.search(where('val') == 1, limit=1)
    res.clear()

    res_again = db.search(where('val') == 1, limit=1)
    assert len(res_again) == 1
