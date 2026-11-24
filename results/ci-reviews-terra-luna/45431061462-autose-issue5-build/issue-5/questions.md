### AutoSE needs more information before it can continue

Please answer the blocking questions below in this thread, then re-trigger with `/autose`.

- **Q-1**: What should “nicer / more pythonic” existence checks provide, including for the reported `1 in db` example?
  _Why it matters:_ INTENT: Different API choices produce different calls and different expected results for the reported example. The existing db.contains API already provides query and document-ID checks, so the desired change cannot be inferred from that capability alone.
  - Make `doc_id in db` check whether that document ID exists, while retaining query checks through `db.contains`.
  - Use membership syntax for both document IDs and query conditions.
  - Keep membership behavior unchanged and improve the existing `db.contains` API or its documentation.
  - Introduce another explicit existence-check API; specify its name and arguments.
- **Q-2**: What measurable behavior should address “It's also slow on my bigger file (~20k docs)”?
  _Why it matters:_ INTENT: A time target, an early-exit requirement, and no performance requirement lead to different acceptance tests.
  - Stop evaluating a query after the first matching document.
  - Meet a specified elapsed-time target for a specified 20,000-document workload and environment.
  - Do not add a performance requirement for this change.
