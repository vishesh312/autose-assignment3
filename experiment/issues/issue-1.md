Title: update()/remove() with doc_ids=['1'] silently do nothing, but get(doc_id='1') works
Type: bug
Labels: bug

Hi, I ran into something confusing with string document ids.

My doc ids come back from a web form / query string so they're strings (`'1'`, `'2'`, ...). Reading works fine with a string id, but updating or removing with the same string id silently does nothing — no error, it just returns `[]` and the document is unchanged.

**Repro**

```python
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

db = TinyDB(storage=MemoryStorage)
db.insert({'x': 1})

print(db.get(doc_id='1'))
# {'x': 1}          <- found it, so '1' is clearly a valid id

print(db.update({'x': 2}, doc_ids=['1']))
# []                <- expected [1]
print(db.all())
# [{'x': 1}]        <- unchanged

print(db.remove(doc_ids=['1']))
# []                <- expected [1]
print(len(db))
# 1                 <- still there

# with an int it works:
print(db.update({'x': 2}, doc_ids=[1]))
# [1]
```

Same thing happens with a JSON file storage and with named tables (`db.table('foo')`).

**Expected**

`update(..., doc_ids=[...])` and `remove(doc_ids=[...])` should accept the same ids that `get(doc_id=...)` / `get(doc_ids=[...])` accept, i.e. `'1'` should hit document 1 and the return value should be the list of ids that were actually updated/removed (`[1]`), same as with ints. Ids that don't exist should still just be skipped like they are now with ints.

The silent no-op is the worst part, I only noticed because a "delete" button in my app didn't do anything.

**Environment**
- tinydb 4.9.0
- Python 3.13.2, macOS 15

(Looks like this was also reported upstream as `msiemens/tinydb` issue `#639`.)
