from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage


def test_ac1_query_equality_different_paths():
    q_home = Query().home.fragment({'city': 'Paris'})
    q_work = Query().work.fragment({'city': 'Paris'})
    assert (q_home == q_work) is False
    assert (q_work == q_home) is False
    assert q_home != q_work


def test_ac1_query_equality_same_path():
    q1 = Query().home.fragment({'city': 'Paris'})
    q2 = Query().home.fragment({'city': 'Paris'})
    assert (q1 == q2) is True
    assert not (q1 != q2)


def test_ac1_query_equality_nested_and_root_paths():
    q_nested1 = Query().user.home.fragment({'city': 'Paris'})
    q_nested2 = Query().user.work.fragment({'city': 'Paris'})
    q_nested3 = Query().user.home.fragment({'city': 'Paris'})
    q_root = Query().fragment({'city': 'Paris'})

    assert (q_nested1 == q_nested2) is False
    assert (q_nested1 == q_nested3) is True
    assert (q_root == Query().home.fragment({'city': 'Paris'})) is False


def test_ac2_search_work_after_home():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    setup_result = db.search(Query().home.fragment({'city': 'Paris'}))
    assert setup_result == [doc]

    result = db.search(Query().work.fragment({'city': 'Paris'}))
    assert result == []


def test_ac2_search_nested_path():
    db = TinyDB(storage=MemoryStorage)
    doc = {'user': {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}}
    db.insert(doc)

    setup_result = db.search(Query().user.home.fragment({'city': 'Paris'}))
    assert setup_result == [doc]

    result = db.search(Query().user.work.fragment({'city': 'Paris'}))
    assert result == []


def test_ac3_search_home_after_work():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    setup_result = db.search(Query().work.fragment({'city': 'Paris'}))
    assert setup_result == []

    result = db.search(Query().home.fragment({'city': 'Paris'}))
    assert result == [doc]


def test_ac4_count_work_after_home():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    setup_result = db.search(Query().home.fragment({'city': 'Paris'}))
    assert setup_result == [doc]

    result = db.count(Query().work.fragment({'city': 'Paris'}))
    assert result == 0


def test_ac5_get_work_after_home():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    setup_result = db.search(Query().home.fragment({'city': 'Paris'}))
    assert setup_result == [doc]

    result = db.get(Query().work.fragment({'city': 'Paris'}))
    assert result is None
