### AutoSE needs more information before it can continue

Please answer the blocking questions below in this thread, then re-trigger with `/autose`.

- **Q-1**: In 'Can existence checks be made nicer / more pythonic? Not sure what the best API is', what API should TinyDB provide for checking document existence beyond document ID membership?
  _Why it matters:_ INTENT: The phrase 'nicer / more pythonic' and admission 'Not sure what the best API is' express a desire for an improved API without specifying it. Two plausible interpretations lead to different acceptance tests: supporting queries via the 'in' operator (e.g. '(where('email') == email) in db') requires acceptance tests asserting boolean results for Query conditions in __contains__, whereas restricting 'in' to document IDs or retaining db.contains(cond) for queries means 'query in db' would either raise a TypeError or not be tested.
  - Implement __contains__ on Table and TinyDB to support both document IDs (e.g., 1 in db) and Query conditions (e.g., (where('x') == 1) in db).
  - Implement __contains__ on Table and TinyDB to support only document IDs (e.g., 1 in db), leaving query existence checks to the existing db.contains(cond) method.
  - Make Table.contains and TinyDB.contains accept a document ID as the first positional argument (e.g., db.contains(1)) without requiring keyword argument doc_id=1.
