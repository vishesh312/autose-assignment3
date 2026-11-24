"""
Tests for issue #5: Support membership test operator (`in`) for document IDs
and queries on tables and databases.
"""

import pytest

from tinydb import Query, TinyDB, where
from tinydb.storages import MemoryStorage


def test_ac1_doc_id_exists():
    """
    AC-1: Given a TinyDB instance with MemoryStorage and a document inserted
    with doc_id=1, evaluating `1 in db` returns True.
    """
    db = TinyDB(storage=MemoryStorage)
    doc_id = db.insert({'name': 'alice'})
    assert doc_id == 1
    assert 1 in db


def test_ac2_doc_id_removed():
    """
    AC-2: Given a TinyDB instance where document 1 was inserted and
    subsequently removed via db.remove(doc_ids=[1]), evaluating `1 in db`
    returns False.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})
    db.remove(doc_ids=[1])
    assert 1 not in db
    assert (1 in db) is False
    assert (999 in db) is False


def test_ac3_query_matches():
    """
    AC-3: Given a TinyDB instance containing {'int': 1, 'char': 'a'},
    evaluating `(where('int') == 1) in db` returns True.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert (where('int') == 1) in db
    assert ((where('int') == 1) in db) is True
    # Also test Query() syntax and custom callable
    assert (Query().char == 'a') in db
    assert (lambda doc: doc.get('int') == 1) in db


def test_ac4_query_no_match():
    """
    AC-4: Given a TinyDB instance containing {'int': 1, 'char': 'a'},
    evaluating `(where('int') == 2) in db` returns False.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    assert (where('int') == 2) not in db
    assert ((where('int') == 2) in db) is False
    assert (Query().char == 'z') not in db


def test_ac5_invalid_operand_type_error():
    """
    AC-5: Given a TinyDB instance containing {'name': 'alice'}, evaluating
    `{'name': 'alice'} in db` raises TypeError.
    """
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'alice'})

    with pytest.raises(TypeError):
        _ = {'name': 'alice'} in db

    # Edge cases: bool, str, list, float, None on db and table
    with pytest.raises(TypeError):
        _ = True in db

    with pytest.raises(TypeError):
        _ = False in db

    with pytest.raises(TypeError):
        _ = 'alice' in db

    with pytest.raises(TypeError):
        _ = [1] in db

    with pytest.raises(TypeError):
        _ = 1.0 in db

    with pytest.raises(TypeError):
        _ = None in db

    table = db.table('custom')
    with pytest.raises(TypeError):
        _ = {'name': 'alice'} in table

    with pytest.raises(TypeError):
        _ = True in table


def test_ac6_named_table_membership():
    """
    AC-6: Given a named table `table = db.table('users')` with document
    {'name': 'bob'} inserted at ID 1 while default table remains empty,
    evaluating `1 in table` returns True.
    """
    db = TinyDB(storage=MemoryStorage)
    table = db.table('users')
    doc_id = table.insert({'name': 'bob'})
    assert doc_id == 1

    assert 1 in table
    assert (1 in table) is True
    assert (1 in db) is False
    assert (2 in table) is False
    assert (where('name') == 'bob') in table
    assert (where('name') == 'alice') not in table
