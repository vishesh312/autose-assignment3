Title: checking if something is in the db is really clunky
Type: vague
Labels: enhancement

Not exactly a bug but it's been bugging me (pun intended). Checking whether a record exists in TinyDB is just awkward compared to everything else in the library which is super pythonic.

Right now I end up writing stuff like

```python
if db.search(User.email == email):
    ...
if len(db.search(User.email == email)) > 0:
    ...
```

or digging through the docs for the right method and the right keyword argument every time. And when I tried the obvious thing it just quietly says no:

```python
>>> 1 in db
False      # there definitely is a document 1 ??
```

which cost me a while of debugging. It's also slow on my bigger file (~20k docs) when I just want a yes/no.

Can existence checks be made nicer / more pythonic? Not sure what the best API is, you know the codebase better, but right now it feels like a footgun.

tinydb 4.9.0, Python 3.11 on Windows
