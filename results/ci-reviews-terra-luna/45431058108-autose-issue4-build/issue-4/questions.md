### AutoSE needs more information before it can continue

Please answer the blocking questions below in this thread, then re-trigger with `/autose`.

- **Q-1**: What should search do when `limit` is a negative integer, such as `limit=-1`?
  _Why it matters:_ INTENT: the issue specifies 'at most N documents' but does not define the domain of N. Plausible choices produce different observable results.
  - Raise ValueError.
  - Return an empty list.
  - Apply Python negative-slice semantics to the matching documents.
