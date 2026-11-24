from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage


def test_ac1_different_paths_compare_unequal():
    q_home = Query().home.fragment({'city': 'Paris'})
    q_work = Query().work.fragment({'city': 'Paris'})
    assert (q_home == q_work) is False


def test_ac1_same_path_and_nested_compatibility():
    # Same path independently constructed compare equal
    q_home1 = Query().home.fragment({'city': 'Paris'})
    q_home2 = Query().home.fragment({'city': 'Paris'})
    assert (q_home1 == q_home2) is True

    # Root-level fragment queries compare equal if same fragment
    q_root1 = Query().fragment({'city': 'Paris'})
    q_root2 = Query().fragment({'city': 'Paris'})
    assert (q_root1 == q_root2) is True
    assert (q_root1 == q_home1) is False

    # Nested field paths compare unequal if paths differ
    q_nested1 = Query().user.home.fragment({'city': 'Paris'})
    q_nested2 = Query().user.work.fragment({'city': 'Paris'})
    assert (q_nested1 == q_nested2) is False


def test_ac2_search_work_after_home():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    res_home = db.search(Query().home.fragment({'city': 'Paris'}))
    assert res_home == [doc]

    res_work = db.search(Query().work.fragment({'city': 'Paris'}))
    assert res_work == []


def test_ac3_search_home_after_work():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    res_work = db.search(Query().work.fragment({'city': 'Paris'}))
    assert res_work == []

    res_home = db.search(Query().home.fragment({'city': 'Paris'}))
    assert res_home == [doc]


def test_ac4_count_work_after_home_search():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    res_home = db.search(Query().home.fragment({'city': 'Paris'}))
    assert res_home == [doc]

    work_count = db.count(Query().work.fragment({'city': 'Paris'}))
    assert work_count == 0


def test_ac5_get_work_after_home_search():
    db = TinyDB(storage=MemoryStorage)
    doc = {'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}
    db.insert(doc)

    res_home = db.search(Query().home.fragment({'city': 'Paris'}))
    assert res_home == [doc]

    work_doc = db.get(Query().work.fragment({'city': 'Paris'}))
    assert work_doc is None
