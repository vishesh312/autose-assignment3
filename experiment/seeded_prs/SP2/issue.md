Title: Feature request: `append` operation for list fields
Type: feature
Labels: enhancement

`tinydb.operations` has `add`, `set`, `increment`, `delete` etc. but nothing for lists, and lists are like half of what I store (tags, event logs...). Right now I have to write my own transform every time:

```python
def append(field, value):
    def transform(doc):
        doc[field].append(value)
    return transform

db.update(append('tags', 'urgent'), Query().id == 42)
```

It would be nice to have this built in, as `tinydb.operations.append(field, value)`, used like the other operations:

```python
from tinydb.operations import append

db.update(append('tags', 'urgent'), Query().name == 'ticket-42')
# {'name': 'ticket-42', 'tags': ['bug']}  ->  {'name': 'ticket-42', 'tags': ['bug', 'urgent']}
```

Some details I'd expect:
- it appends `value` as one element (so `append('tags', ['a', 'b'])` adds a nested list, it doesn't extend — like `list.append`)
- if the document doesn't have the field yet, create it as a one-element list (`[value]`) instead of blowing up with a KeyError. Half my older docs don't have a `tags` key.
- works with both `cond` and `doc_ids=` like the other operations, and obviously the change should be saved to the json file

(This was asked a long time ago upstream in `msiemens/tinydb` issue `#66` too, would still be useful!)

tinydb 4.9.0, Python 3.12
