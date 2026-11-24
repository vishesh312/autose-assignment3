from tinydb import Query, TinyDB
from tinydb.operations import append
from tinydb.storages import JSONStorage, MemoryStorage


def test_ac1_append_to_existing_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': ['bug', 'urgent']}]


def test_ac1_append_multiple_items_preserves_order():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    db.update(append('tags', 'feature'), Query().name == 'ticket-42')
    assert db.all() == [
        {'name': 'ticket-42', 'tags': ['bug', 'urgent', 'feature']}
    ]


def test_ac2_append_nested_list_to_empty_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': []})
    db.update(append('tags', ['a', 'b']), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': [['a', 'b']]}]


def test_ac2_append_nested_empty_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': []})
    db.update(append('tags', []), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': [[]]}]


def test_ac3_append_creates_missing_field():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42'})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': ['urgent']}]


def test_ac3_append_missing_field_with_nested_list():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42'})
    db.update(append('tags', ['urgent']), Query().name == 'ticket-42')
    assert db.all() == [{'name': 'ticket-42', 'tags': [['urgent']]}]


def test_ac4_cond_updates_only_matching_document():
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


def test_ac4_cond_no_match_leaves_documents_unchanged():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.insert({'name': 'ticket-43', 'tags': ['other']})
    db.update(append('tags', 'urgent'), cond=Query().name == 'ticket-999')
    assert db.get(Query().name == 'ticket-42') == {
        'name': 'ticket-42',
        'tags': ['bug'],
    }
    assert db.get(Query().name == 'ticket-43') == {
        'name': 'ticket-43',
        'tags': ['other'],
    }


def test_ac5_doc_ids_updates_only_selected_id():
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


def test_ac5_doc_ids_empty_list_updates_nothing():
    db = TinyDB(storage=MemoryStorage)
    target_id = db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.insert({'name': 'ticket-43', 'tags': ['other']})
    db.update(append('tags', 'urgent'), doc_ids=[])
    assert db.get(doc_id=target_id) == {
        'name': 'ticket-42',
        'tags': ['bug'],
    }
    assert db.get(Query().name == 'ticket-43') == {
        'name': 'ticket-43',
        'tags': ['other'],
    }


def test_ac6_json_storage_persistence_after_reopen(tmp_path):
    db_path = str(tmp_path / 'append.json')
    db = TinyDB(db_path, storage=JSONStorage)
    db.insert({'name': 'ticket-42', 'tags': ['bug']})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    db.close()

    reopened = TinyDB(db_path, storage=JSONStorage)
    assert reopened.all() == [
        {'name': 'ticket-42', 'tags': ['bug', 'urgent']}
    ]
    reopened.close()


def test_ac6_json_storage_missing_field_persisted(tmp_path):
    db_path = str(tmp_path / 'append_missing.json')
    db = TinyDB(db_path, storage=JSONStorage)
    db.insert({'name': 'ticket-42'})
    db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
    db.close()

    reopened = TinyDB(db_path, storage=JSONStorage)
    assert reopened.all() == [{'name': 'ticket-42', 'tags': ['urgent']}]
    reopened.close()
