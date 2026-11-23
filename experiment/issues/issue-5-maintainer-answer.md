Thanks for the report! Agreed that `1 in db` quietly returning `False` is a footgun (it currently falls back to iterating the documents and comparing each document to `1`). Let's keep the scope small and just make the `in` operator do the obvious thing. Concretely:

1. **Doc IDs:** `doc_id in table` should be `True` if and only if a document with that (int) ID exists, i.e. exactly what `table.contains(doc_id=doc_id)` returns. So `1 in db` is `True` after the first insert and `False` again after `db.remove(doc_ids=[1])`.
2. **Queries:** `query in table` (anything callable, e.g. `Query().email == x`) should be `True` if and only if at least one document matches, i.e. exactly `table.contains(query)`.
3. **Anything else** (for example a dict / a document like `{'name': 'alice'} in db`) should raise a `TypeError` instead of silently returning a result. We don't want to support "is this exact document in the table" semantics.
4. It has to work on both `TinyDB` (the default table) and on named tables from `db.table('...')`. Note that magic methods aren't forwarded by `TinyDB.__getattr__`, so the database needs its own forwarding like `__len__`/`__iter__` already have.

No new methods, no changes to `contains()` itself, and the speed of large tables is out of scope for this issue (that would need indexes, which TinyDB doesn't have). Please add tests for the four points above.
