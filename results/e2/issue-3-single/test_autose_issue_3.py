from tinydb import Query, TinyDB
from tinydb.operations import append
from tinydb.storages import JSONStorage, MemoryStorage


def test_ac1_append_existing_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': ['bug', 'urgent']}]


def test_ac2_append_nested_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': []})
    db.update(append('tags', ['a', 'b']), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': [['a', 'b']]}]


def test_ac3_append_missing_field():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42'})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': ['urgent']}]


def test_ac3_append_missing_field_separate_instances():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42'})
    db.insert({'name': 'ticket-43'})
    db.update(append('tags', 'urgent'))
    assert db.all() == [
        {'name': 'ticket-42', 'tags': ['urgent']},
        {'name': 'ticket-43', 'tags': ['urgent']},
    ]
    # Appending to one document should not affect the other
    db.update(append('tags', 'extra'), Query().name == 'ticket-42')
    assert db.get(Query().name == 'ticket-42') == {
        'name': 'ticket-42',
        'tags': ['urgent', 'extra'],
    }
    assert db.get(Query().name == 'ticket-43') == {
        'name': 'ticket-43',
        'tags': ['urgent'],
    }


def test_ac4_append_with_cond():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.insert({'name': 'ticket-43', 'tags': ['other']})
    db.update(append('tags', 'urgent'), cond=Query().name == 'ticket-42')
    assert db.get(Query().name == 'ticket-42') == {
        'name': 'ticket-42',
        'tags': ['bug', 'urgent'],
    }
    assert db.get(Query().name == 'ticket-43') == {
        'name': 'ticket-43',
        'tags': ['other'],
    }


def test_ac5_append_with_doc_ids():
    db = TinyDB(storage=MemoryStorage)
    target_id = db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.insert({'name': 'ticket-43', 'tags': ['other']})
    db.update(append('tags', 'urgent'), doc_ids=[target_id])
    assert db.get(doc_id=target_id) == {
        'name': 'ticket-42',
        'tags': ['bug', 'urgent'],
    }
    assert db.get(Query().name == 'ticket-43') == {
        'name': 'ticket-43',
        'tags': ['other'],
    }


def test_ac6_append_json_persistence(tmp_path):
    path = str(tmp_path / 'append.json')
    db = TinyDB(path, storage=JSONStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    db.close()

    db_reopened = TinyDB(path, storage=JSONStorage)
    assert db_reopened.all() == [
        {'name': 'ticket-42', 'tags': ['bug', 'urgent']}
    ]
    db_reopened.close()
