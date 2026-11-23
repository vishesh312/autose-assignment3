"""Hidden acceptance tests for issue 3: an ``append`` update operation in
``tinydb.operations``.
"""
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def test_append_adds_value_to_list_field_of_matching_docs():
    from tinydb.operations import append

    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'x', 'tags': ['a']})
    db.insert({'name': 'y', 'tags': ['a']})

    updated = db.update(append('tags', 'b'), Query().name == 'x')

    assert updated == [1]
    assert db.get(doc_id=1)['tags'] == ['a', 'b']
    assert db.get(doc_id=2)['tags'] == ['a']


def test_append_creates_list_when_field_missing():
    from tinydb.operations import append

    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'x'})

    db.update(append('tags', 'first'), doc_ids=[1])

    assert db.get(doc_id=1)['tags'] == ['first']


def test_append_adds_list_as_single_element_and_accumulates():
    from tinydb.operations import append

    db = TinyDB(storage=MemoryStorage)
    db.insert({'items': [1]})

    db.update(append('items', [2, 3]))
    db.update(append('items', {'k': 'v'}))

    assert db.all()[0]['items'] == [1, [2, 3], {'k': 'v'}]


def test_append_persists_to_json_file(tmp_path):
    from tinydb.operations import append

    path = tmp_path / 'db.json'
    with TinyDB(path) as db:
        db.insert({'log': []})
        db.update(append('log', 'one'), doc_ids=[1])
        db.update(append('log', 'two'), doc_ids=[1])

    with TinyDB(path) as db:
        assert db.get(doc_id=1)['log'] == ['one', 'two']
