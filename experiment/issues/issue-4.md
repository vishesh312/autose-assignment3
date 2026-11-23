Title: Add a `limit` argument to search()
Type: feature
Labels: enhancement

Hey, love the project :)

I often only need the first few matching documents (e.g. "show the 5 oldest open tasks" in a little CLI). Right now I do `db.search(q)[:5]`, which works but reads a bit odd and every call site has to remember to slice.

Could `search` take an optional `limit`?

```python
from tinydb import TinyDB, Query

db = TinyDB('tasks.json')
Task = Query()

db.search(Task.status == 'open', limit=5)   # at most 5 docs
db.search(Task.status == 'open')            # unchanged, all matches
```

What I'd expect:
- `limit=N` returns at most N documents, the first N matches in the normal order (document id / insertion order), same order `search` already uses
- `limit=None` (the default) means no limit, so existing code doesn't change
- if there are fewer matches than `limit`, just return all of them
- should work on `db.table('x').search(...)` too, not just the default table
- please make sure it plays nice with the query cache — I don't want `search(q, limit=1)` followed by `search(q)` to suddenly give me only 1 result (or the other way round)

There was an old PR for this upstream (`msiemens/tinydb` `#508` / `#509`) that never got merged, so maybe there was a reason, but it'd be handy.

tinydb 4.9.0, Python 3.13
