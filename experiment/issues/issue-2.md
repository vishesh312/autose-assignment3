Title: search() with fragment() returns wrong results when the same fragment is used on another field
Type: bug
Labels: bug

I'm using `Query().fragment()` on nested fields and getting results that don't match the query. Looks like a caching problem because the first search works and the second one returns exactly the same documents as the first.

**Repro**

```python
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

db = TinyDB(storage=MemoryStorage)
db.insert({'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}})

print(db.search(Query().home.fragment({'city': 'Paris'})))
# [{'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}]   <- correct

print(db.search(Query().work.fragment({'city': 'Paris'})))
# [{'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}]   <- WRONG, work.city is Rome, should be []

# calling the query directly gives the right answer:
q = Query().work.fragment({'city': 'Paris'})
print(q(db.all()[0]))
# False
```

`db.count(...)` and `db.get(...)` are wrong the same way (count says 1 for the `work` query). If I call `db.clear_cache()` between the two searches, the second one is correct, which is why I think it's the query cache.

I also noticed the two queries compare equal, which seems wrong since they look at different fields:

```python
>>> Query().home.fragment({'city': 'Paris'}) == Query().work.fragment({'city': 'Paris'})
True
```

Other query types (`==`, `exists()`, `any()`...) on different fields are not equal, so I guess fragment just forgets about the field path?

**Environment**
- tinydb 4.9.0
- Python 3.13.2 on Ubuntu 24.04
