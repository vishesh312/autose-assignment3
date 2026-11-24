from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_limit_returns_first_n_matching_documents():
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


def test_ac1_limit_equals_total_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})
    db.insert({'name': 'doc3', 'val': 1})

    results = db.search(where('val') == 1, limit=3)
    assert len(results) == 3
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1},
        {'name': 'doc3', 'val': 1},
    ]


def test_ac1_limit_with_interleaved_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 2})
    db.insert({'name': 'doc3', 'val': 1})
    db.insert({'name': 'doc4', 'val': 1})

    results = db.search(where('val') == 1, limit=2)
    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc3', 'val': 1},
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


def test_ac2_limit_exceeding_on_empty_table():
    db = TinyDB(storage=MemoryStorage)
    results = db.search(where('val') == 1, limit=5)
    assert results == []


def test_ac3_limit_zero_returns_empty_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})

    results = db.search(where('val') == 1, limit=0)
    assert results == []


def test_ac3_limit_zero_on_empty_table():
    db = TinyDB(storage=MemoryStorage)
    results = db.search(where('val') == 1, limit=0)
    assert results == []


def test_ac4_limit_none_and_omitted_returns_all_matches():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 10})
    db.insert({'name': 'doc2', 'val': 10})
    db.insert({'name': 'doc3', 'val': 20})

    res_none = db.search(where('val') == 10, limit=None)
    res_omitted = db.search(where('val') == 10)

    assert res_none == res_omitted
    assert len(res_none) == 2
    assert res_none == [
        {'name': 'doc1', 'val': 10},
        {'name': 'doc2', 'val': 10},
    ]


def test_ac5_table_search_with_limit():
    db = TinyDB(storage=MemoryStorage)
    tasks_table = db.table('tasks')
    tasks_table.insert({'task': 't1', 'status': 'open'})
    tasks_table.insert({'task': 't2', 'status': 'open'})
    tasks_table.insert({'task': 't3', 'status': 'open'})

    results = tasks_table.search(where('status') == 'open', limit=1)
    assert len(results) == 1
    assert results == [{'task': 't1', 'status': 'open'}]


def test_ac5_table_search_limit_multiple():
    db = TinyDB(storage=MemoryStorage)
    tasks_table = db.table('tasks')
    tasks_table.insert({'task': 't1', 'status': 'open'})
    tasks_table.insert({'task': 't2', 'status': 'open'})
    tasks_table.insert({'task': 't3', 'status': 'open'})

    results = tasks_table.search(where('status') == 'open', limit=2)
    assert len(results) == 2
    assert results == [
        {'task': 't1', 'status': 'open'},
        {'task': 't2', 'status': 'open'},
    ]


def test_ac6_query_cache_isolation_across_different_limits():
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


def test_ac6_query_cache_unlimited_first_then_limited():
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
