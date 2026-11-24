from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_limit_returns_first_n_matches():
    """
    AC-1: db.search(where('val') == 1, limit=2) returns exactly the first 2
    matching documents in document ID insertion order.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})
    db.insert({'name': 'doc3', 'val': 1})

    results = db.search(where('val') == 1, limit=2)
    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1}
    ]


def test_ac2_limit_exceeding_total_matches():
    """
    AC-2: db.search(where('val') == 1, limit=5) when matches are fewer than
    limit returns all matches without error or truncation.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})

    results = db.search(where('val') == 1, limit=5)
    assert len(results) == 2
    assert results == [
        {'name': 'doc1', 'val': 1},
        {'name': 'doc2', 'val': 1}
    ]


def test_ac3_limit_zero_returns_empty_list():
    """
    AC-3: db.search(where('val') == 1, limit=0) returns an empty list.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 1})
    db.insert({'name': 'doc2', 'val': 1})

    results = db.search(where('val') == 1, limit=0)
    assert results == []


def test_ac4_limit_none_preserves_default_behavior():
    """
    AC-4: db.search(where('val') == 10, limit=None) preserves default search
    behavior matching db.search(where('val') == 10).
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'doc1', 'val': 10})
    db.insert({'name': 'doc2', 'val': 10})
    db.insert({'name': 'doc3', 'val': 20})

    res_none = db.search(where('val') == 10, limit=None)
    res_default = db.search(where('val') == 10)
    assert res_none == res_default
    assert len(res_none) == 2


def test_ac5_non_default_table_limit():
    """
    AC-5: db.table('tasks').search(where('status') == 'open', limit=1) returns
    only the first matching document from the non-default table.
    """
    db = TinyDB(storage=MemoryStorage)
    tasks = db.table('tasks')
    tasks.insert({'task': 't1', 'status': 'open'})
    tasks.insert({'task': 't2', 'status': 'open'})
    tasks.insert({'task': 't3', 'status': 'open'})

    results = tasks.search(where('status') == 'open', limit=1)
    assert len(results) == 1
    assert results == [{'task': 't1', 'status': 'open'}]


def test_ac6_query_cache_isolation():
    """
    AC-6: The sequence limit=1, then unlimited, then limit=1 serves each
    query without result truncation leakage across calls.
    """
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


def test_ac6_cache_isolation_unlimited_then_limited():
    """
    AC-6 edge case: Cache isolation when unconstrained query runs first,
    populating cache, followed by queries with varying limits.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 1})
    db.insert({'val': 1})
    db.insert({'val': 1})

    res1 = db.search(where('val') == 1)
    res2 = db.search(where('val') == 1, limit=2)
    res3 = db.search(where('val') == 1, limit=1)
    res4 = db.search(where('val') == 1)

    assert len(res1) == 3
    assert len(res2) == 2
    assert len(res3) == 1
    assert len(res4) == 3


def test_ac6_result_list_mutation_isolation():
    """
    AC-6 edge case: Mutating returned result list does not mutate cached
    results.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 1})
    db.insert({'val': 1})

    res1 = db.search(where('val') == 1, limit=1)
    assert len(res1) == 1
    res1.clear()

    res2 = db.search(where('val') == 1, limit=1)
    assert len(res2) == 1
