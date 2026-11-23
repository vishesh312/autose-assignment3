# Spec — issue #2: search() with fragment() returns wrong results for another field

## Summary

After `db.search(Query().home.fragment(F))`, a search with the same fragment on a different field (`Query().work.fragment(F)`) returns the first query's documents instead of its own matches. `count()` is wrong in the same way. Evaluating the query directly is correct and `clear_cache()` hides the problem, so the defect is in how fragment query results are served from the table's query cache. `search`, `count` and `get` must return the correct documents for fragment queries regardless of which queries ran before.

Issue type: **bug**

## Source excerpts

- **SRC-1:** "`print(db.search(Query().work.fragment({'city': 'Paris'})))` … `<- WRONG, work.city is Rome, should be []`"
- **SRC-2:** "`db.count(...)` and `db.get(...)` are wrong the same way (count says 1 for the `work` query)."
- **SRC-3:** "If I call `db.clear_cache()` between the two searches, the second one is correct, which is why I think it's the query cache."

## Requirements

| ID | Requirement | Provenance | Sources |
|---|---|---|---|
| REQ-1 | `search` with a fragment query returns exactly the documents for which the query is true, independent of previously run queries. | STATED | SRC-1, SRC-3 |
| REQ-2 | `count` and `get` with fragment queries are correct in the same situation. | STATED | SRC-2 |
| REQ-3 | Fragment queries combined with other queries (`&`, `|`, `~`) are also correct. | DERIVED | SRC-1 |
| REQ-4 | Results reflect the current table contents after updates. | DERIVED | SRC-3 |

## Acceptance criteria

- **AC-1** (REQ-1) — *Given* a document `{'home': {'city': 'Paris'}, 'work': {'city': 'Rome'}}` — *when* `search(Query().home.fragment({'city': 'Paris'}))` and then `search(Query().work.fragment({'city': 'Paris'}))` run (repeatedly) — *then* the first returns the document and the second returns `[]`. *Observable:* search results.
- **AC-2** (REQ-2) — *Given* the same document — *when* `count`/`get` run with the `work` fragment after the `home` fragment — *then* `count == 0` and `get` returns `None`. *Observable:* return values.
- **AC-3** (REQ-3) — *Given* the same document — *when* a fragment query is combined with `Query().home.exists()` using `&` — *then* the result is correct for each field. *Observable:* search results.
- **AC-4** (REQ-4) — *Given* a cached-looking sequence of fragment searches — *when* the document is updated so the `work` fragment matches — *then* the next search returns it. *Observable:* search results.

## Open questions

None.

## Out of scope

- Changing how `Query` objects compare or hash in general (public behaviour of `Query`); the reported user-facing defect is the wrong search/count/get result.
- Query-cache capacity or eviction policy.

## Injection findings

None.
