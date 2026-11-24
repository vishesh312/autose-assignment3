from pathlib import Path

from tinydb import JSONStorage, TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_update_single_string_id(tmp_path: Path) -> None:
    configs = [
        ('memory', 'default'),
        ('memory', 'foo'),
        ('json', 'default'),
        ('json', 'foo'),
    ]
    for storage_type, table_type in configs:
        if storage_type == 'memory':
            db = TinyDB(storage=MemoryStorage)
        else:
            db = TinyDB(
                tmp_path / f'ac1_{table_type}.json',
                storage=JSONStorage
            )
        try:
            table = db if table_type == 'default' else db.table('foo')
            doc_id = table.insert({'x': 1})
            assert doc_id == 1

            ret = table.update({'x': 2}, doc_ids=['1'])

            assert ret == [1]
            assert len(ret) == 1
            assert type(ret[0]) is int
            assert table.get(doc_id=1) == {'x': 2}
            assert len(table) == 1
        finally:
            db.close()


def test_ac1_update_query_cache_invalidation() -> None:
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1
        assert len(db.search(where('x') == 1)) == 1

        ret = db.update({'x': 2}, doc_ids=['1'])
        assert ret == [1]

        assert len(db.search(where('x') == 1)) == 0
        assert len(db.search(where('x') == 2)) == 1
    finally:
        db.close()


def test_ac2_remove_single_string_id(tmp_path: Path) -> None:
    configs = [
        ('memory', 'default'),
        ('memory', 'foo'),
        ('json', 'default'),
        ('json', 'foo'),
    ]
    for storage_type, table_type in configs:
        if storage_type == 'memory':
            db = TinyDB(storage=MemoryStorage)
        else:
            db = TinyDB(
                tmp_path / f'ac2_{table_type}.json',
                storage=JSONStorage
            )
        try:
            table = db if table_type == 'default' else db.table('foo')
            doc_id = table.insert({'x': 1})
            assert doc_id == 1

            ret = table.remove(doc_ids=['1'])

            assert ret == [1]
            assert len(ret) == 1
            assert type(ret[0]) is int
            assert table.all() == []
            assert len(table) == 0
        finally:
            db.close()


def test_ac2_remove_query_cache_invalidation() -> None:
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1
        assert len(db.search(where('x') == 1)) == 1

        ret = db.remove(doc_ids=['1'])
        assert ret == [1]

        assert len(db.search(where('x') == 1)) == 0
    finally:
        db.close()


def test_ac3_update_mixed_string_and_int_targets() -> None:
    db = TinyDB(storage=MemoryStorage)
    try:
        id1 = db.insert({'x': 1})
        id2 = db.insert({'x': 2})
        id3 = db.insert({'x': 3})
        assert (id1, id2, id3) == (1, 2, 3)

        ret = db.update({'x': 9}, doc_ids=['1', 2, '99', 100])

        assert len(ret) == 2
        assert set(ret) == {1, 2}
        assert all(type(x) is int for x in ret)
        assert db.get(doc_id=1) == {'x': 9}
        assert db.get(doc_id=2) == {'x': 9}
        assert db.get(doc_id=3) == {'x': 3}
        assert len(db) == 3
    finally:
        db.close()


def test_ac4_remove_mixed_string_and_int_targets() -> None:
    db = TinyDB(storage=MemoryStorage)
    try:
        id1 = db.insert({'x': 1})
        id2 = db.insert({'x': 2})
        id3 = db.insert({'x': 3})
        assert (id1, id2, id3) == (1, 2, 3)

        ret = db.remove(doc_ids=['1', 2, '99', 100])

        assert len(ret) == 2
        assert set(ret) == {1, 2}
        assert all(type(x) is int for x in ret)
        assert db.get(doc_id=1) is None
        assert db.get(doc_id=2) is None
        assert db.get(doc_id=3) == {'x': 3}
        assert len(db) == 1
    finally:
        db.close()


def test_ac5_update_all_missing_targets() -> None:
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1

        ret = db.update({'x': 9}, doc_ids=['99', 100])

        assert ret == []
        assert db.all() == [{'x': 1}]
        assert db.get(doc_id=1) == {'x': 1}
    finally:
        db.close()


def test_ac6_remove_all_missing_targets() -> None:
    db = TinyDB(storage=MemoryStorage)
    try:
        doc_id = db.insert({'x': 1})
        assert doc_id == 1

        ret = db.remove(doc_ids=['99', 100])

        assert ret == []
        assert db.all() == [{'x': 1}]
        assert db.get(doc_id=1) == {'x': 1}
    finally:
        db.close()
