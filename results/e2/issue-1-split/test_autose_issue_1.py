import pytest

from tinydb import JSONStorage, TinyDB, where
from tinydb.storages import MemoryStorage


@pytest.mark.parametrize('storage_backend', ['memory', 'json'])
@pytest.mark.parametrize('table_name', ['default', 'foo'])
def test_ac1_update_doc_id_string(storage_backend, table_name, tmp_path):
    if storage_backend == 'memory':
        db = TinyDB(storage=MemoryStorage)
    else:
        db = TinyDB(tmp_path / 'test.json', storage=JSONStorage)
    try:
        table = db if table_name == 'default' else db.table('foo')
        doc_id = table.insert({'x': 1})
        assert doc_id == 1

        result = table.update({'x': 2}, doc_ids=['1'])

        assert result == [1]
        assert type(result[0]) is int
        assert table.get(doc_id=1) == {'x': 2}
        assert len(table) == 1
    finally:
        db.close()


def test_ac1_update_callable_with_string_id():
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1

        def updater(doc):
            doc['x'] = 2

        result = db.update(updater, doc_ids=['1'])

        assert result == [1]
        assert type(result[0]) is int
        assert db.get(doc_id=1) == {'x': 2}
        assert len(db) == 1
    finally:
        db.close()


def test_ac1_update_query_cache_invalidation():
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1
        query = where('x') == 1
        assert len(db.search(query)) == 1

        result = db.update({'x': 2}, doc_ids=['1'])

        assert result == [1]
        assert type(result[0]) is int
        assert db.search(query) == []
        assert db.search(where('x') == 2) == [{'x': 2}]
    finally:
        db.close()


@pytest.mark.parametrize('storage_backend', ['memory', 'json'])
@pytest.mark.parametrize('table_name', ['default', 'foo'])
def test_ac2_remove_doc_id_string(storage_backend, table_name, tmp_path):
    if storage_backend == 'memory':
        db = TinyDB(storage=MemoryStorage)
    else:
        db = TinyDB(tmp_path / 'test.json', storage=JSONStorage)
    try:
        table = db if table_name == 'default' else db.table('foo')
        doc_id = table.insert({'x': 1})
        assert doc_id == 1

        result = table.remove(doc_ids=['1'])

        assert result == [1]
        assert type(result[0]) is int
        assert table.all() == []
        assert len(table) == 0
    finally:
        db.close()


def test_ac2_remove_query_cache_invalidation():
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1
        query = where('x') == 1
        assert len(db.search(query)) == 1

        result = db.remove(doc_ids=['1'])

        assert result == [1]
        assert type(result[0]) is int
        assert db.search(query) == []
        assert len(db) == 0
    finally:
        db.close()


def test_ac3_update_mixed_existing_and_nonexistent_ids():
    db = TinyDB(storage=MemoryStorage)
    try:
        id1 = db.insert({'x': 1})
        id2 = db.insert({'x': 2})
        id3 = db.insert({'x': 3})
        assert id1 == 1 and id2 == 2 and id3 == 3

        result = db.update({'x': 9}, doc_ids=['1', 2, '99', 100])

        assert len(result) == 2
        assert set(result) == {1, 2}
        assert all(type(doc_id) is int for doc_id in result)
        assert db.get(doc_id=1) == {'x': 9}
        assert db.get(doc_id=2) == {'x': 9}
        assert db.get(doc_id=3) == {'x': 3}
        assert len(db) == 3
    finally:
        db.close()


def test_ac4_remove_mixed_existing_and_nonexistent_ids():
    db = TinyDB(storage=MemoryStorage)
    try:
        id1 = db.insert({'x': 1})
        id2 = db.insert({'x': 2})
        id3 = db.insert({'x': 3})
        assert id1 == 1 and id2 == 2 and id3 == 3

        result = db.remove(doc_ids=['1', 2, '99', 100])

        assert len(result) == 2
        assert set(result) == {1, 2}
        assert all(type(doc_id) is int for doc_id in result)
        assert db.get(doc_id=1) is None
        assert db.get(doc_id=2) is None
        assert db.get(doc_id=3) == {'x': 3}
        assert len(db) == 1
    finally:
        db.close()


def test_ac5_update_all_nonexistent_ids():
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1

        result = db.update({'x': 9}, doc_ids=['99', 100])

        assert result == []
        assert db.all() == [{'x': 1}]
        assert db.get(doc_id=1) == {'x': 1}
    finally:
        db.close()


def test_ac6_remove_all_nonexistent_ids():
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1

        result = db.remove(doc_ids=['99', 100])

        assert result == []
        assert db.all() == [{'x': 1}]
        assert db.get(doc_id=1) == {'x': 1}
    finally:
        db.close()
