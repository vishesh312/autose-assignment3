import pytest
from tinydb import Query, TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_in_db_doc_id_exists():
    db = TinyDB(storage=MemoryStorage)
    doc_id = db.insert({'name': 'alice'})
    assert doc_id == 1
    assert (1 in db) is True


def test_ac1_in_db_doc_id_missing():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    assert (99 in db) is False


def test_ac2_in_db_doc_id_removed():
    db = TinyDB(storage=MemoryStorage)
    doc_id = db.insert({'name': 'alice'})
    assert doc_id == 1
    db.remove(doc_ids=[1])
    assert (1 in db) is False


def test_ac3_in_db_matching_query():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert ((where('int') == 1) in db) is True


def test_ac3_in_db_matching_query_instance_and_callable():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    q = Query()
    assert ((q.int == 1) in db) is True
    assert ((lambda doc: doc.get('int') == 1) in db) is True


def test_ac4_in_db_non_matching_query():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert ((where('int') == 2) in db) is False


def test_ac4_in_db_non_matching_callable():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert ((lambda doc: doc.get('int') == 2) in db) is False


def test_ac5_in_db_doc_dict_raises_type_error():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    with pytest.raises(TypeError):
        {'name': 'alice'} in db


def test_ac5_in_db_invalid_types_raise_type_error():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    invalid_operands = [
        True,
        False,
        '1',
        1.0,
        None,
        [1],
        (1,),
    ]
    for operand in invalid_operands:
        with pytest.raises(TypeError):
            operand in db


def test_ac6_in_named_table_doc_id_exists():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('users')
    doc_id = table.insert({'name': 'bob'})
    assert doc_id == 1
    assert (1 in table) is True
    assert (1 in db) is False


def test_ac6_in_named_table_queries_and_invalid_types():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('users')
    table.insert({'name': 'bob'})
    assert ((where('name') == 'bob') in table) is True
    assert ((where('name') == 'alice') in table) is False
    with pytest.raises(TypeError):
        {'name': 'bob'} in table
    with pytest.raises(TypeError):
        True in table
    table.remove(doc_ids=[1])
    assert (1 in table) is False
