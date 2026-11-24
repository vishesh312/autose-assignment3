import pytest

from tinydb import Query, TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_existing_doc_id_in_db():
    db = TinyDB(storage=MemoryStorage)
    doc_id = db.insert({'name': 'alice'})
    assert doc_id == 1
    assert 1 in db


def test_ac1_multiple_doc_ids_in_db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    db.insert({'name': 'bob'})
    assert 1 in db
    assert 2 in db


def test_ac2_removed_doc_id_not_in_db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    db.remove(doc_ids=[1])
    assert (1 in db) is False


def test_ac2_never_inserted_doc_id_not_in_db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    assert (999 in db) is False


def test_ac3_matching_query_where_in_db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert ((where('int') == 1) in db) is True


def test_ac3_matching_query_instance_or_callable_in_db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert ((Query().char == 'a') in db) is True

    def query_func(doc):
        return doc.get('int') == 1

    assert (query_func in db) is True


def test_ac4_non_matching_query_where_in_db():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert ((where('int') == 2) in db) is False


def test_ac4_non_matching_query_empty_db():
    db = TinyDB(storage=MemoryStorage)
    assert ((where('int') == 1) in db) is False
    assert ((Query().char == 'a') in db) is False


def test_ac5_document_dict_raises_type_error():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    with pytest.raises(TypeError):
        _ = {'name': 'alice'} in db


def test_ac5_invalid_types_raise_type_error():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    with pytest.raises(TypeError):
        _ = True in db
    with pytest.raises(TypeError):
        _ = False in db
    with pytest.raises(TypeError):
        _ = 'alice' in db
    with pytest.raises(TypeError):
        _ = 1.0 in db
    with pytest.raises(TypeError):
        _ = [1] in db
    with pytest.raises(TypeError):
        _ = None in db


def test_ac6_named_table_contains_doc_id():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('users')
    doc_id = table.insert({'name': 'bob'})
    assert doc_id == 1
    assert 1 in table
    assert (1 in db) is False


def test_ac6_named_table_queries_and_removal():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('users')
    table.insert({'name': 'bob'})
    assert ((where('name') == 'bob') in table) is True
    assert ((where('name') == 'alice') in table) is False
    with pytest.raises(TypeError):
        _ = {'name': 'bob'} in table
    table.remove(doc_ids=[1])
    assert (1 in table) is False
