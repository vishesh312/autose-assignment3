## AutoSE review (round 1): **APPROVE**

The pull request correctly implements the requested `limit` argument for `Table.search()`, defaulting to `None` to preserve backwards compatibility. The query cache correctly stores the full match list and slices the result on demand, ensuring complete cache isolation between limited and unlimited queries across default and named tables. Existing test suites, type checking, and newly added edge-case probe tests all pass cleanly.

# Pull Request Review: Issue #4 - Add a `limit` argument to `search()`

## Verdict
**APPROVE**

---

## Summary
The pull request correctly implements the requested `limit` argument for `Table.search()`, defaulting to `None` to preserve backwards compatibility. The query cache stores the complete match list and slices the result on demand, ensuring complete cache isolation between limited and unlimited queries across default and named tables. Existing test suites, type checking, and newly added edge-case probe tests all pass cleanly.

---

## Important Findings
None.

---

## Pre-existing Findings
None.

---

## Nits
- **[nit-negative-limit-slicing](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/pr/tinydb/table.py#L252)** (`code`): Passing a negative integer for `limit` (e.g. `limit=-1`) is not validated and gets passed directly to Python slice indexing `[:limit]`, returning all matching documents except the last N instead of returning an empty list or raising a `ValueError`.
  - *Evidence*: Calling `db.search(where('v') > 0, limit=-1)` on 3 matching documents returned 2 documents (`[1, 2]`).
  - *Suggested Fix*: If negative limits should not be treated as negative slice offsets, add validation `if limit is not None and limit < 0: raise ValueError('limit must be non-negative')` (or clamp negative limits to 0).

---

## Previous-Round Status
Round 1 review: no previous rounds.

---

## Risk Hypotheses Tested
1. **Hypothesis**: The change is wrong if calling `search(cond, limit=K)` on a cold cache stores truncated results in `_query_cache`, causing subsequent unlimited searches `search(cond)` or `count(cond)` to return only K results.
   - *How tested*: Wrote and executed `test_probe_cache_isolation_and_count` in [test_probe_limit.py](file:///var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/test_probe_limit.py), calling `db.search(q, limit=1)` followed by `db.count(q)` and `db.search(q)` on a 3-item match set.
   - *Outcome*: **Refuted** (`search(q, limit=1)` returned 1 item, while subsequent `count(q)` returned 3 and `search(q)` returned all 3 items).

2. **Hypothesis**: The change is wrong if `search(cond, limit=N)` behaves inconsistently when backed by persistent `JSONStorage` or fails to invalidate cached query slices after writes (`insert`, `update`, `delete`).
   - *How tested*: Wrote and executed `test_probe_json_storage_and_mutation` in [test_probe_limit.py](file:///var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/test_probe_limit.py) using `JSONStorage`, verifying limit slicing across disk persist/reopen cycles and verifying cache invalidation upon inserting new documents.
   - *Outcome*: **Refuted** (JSONStorage persistence works identically, disk reload retains data, and writes properly invalidate the cache so subsequent limited searches reflect newly inserted documents).

3. **Hypothesis**: The change is wrong if the new test suite `tests/test_autose_issue_4.py` would pass even on the base branch without the PR's implementation.
   - *How tested*: Inspected base ref `edff96aeb2616402e9489d46e90a592c05565621:tinydb/table.py` and executed [probe_base_behavior.py](file:///var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/probe_base_behavior.py) to verify whether `Table.search` previously accepted `limit`.
   - *Outcome*: **Refuted** (On the base branch, `Table.search` only took `self, cond: QueryLike`. Any call with `limit=...` raises `TypeError: Table.search() got an unexpected keyword argument 'limit'`. The new tests strictly fail on the base branch).

4. **Hypothesis**: The change is wrong if uncacheable queries (`cond.is_cacheable() == False`) fail to respect the `limit` argument when evaluated directly without caching.
   - *How tested*: Wrote and executed `test_probe_uncacheable_query` in [test_probe_limit.py](file:///var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/test_probe_limit.py) with a custom query object returning `is_cacheable() == False`.
   - *Outcome*: **Refuted** (`search` properly returned `docs[:limit]` even when `is_cacheable()` was `False`).

5. **Hypothesis**: The change is wrong if passing a negative limit (e.g. `limit=-1`) causes unexpected truncation by returning all documents except the last N instead of raising a ValueError or returning an empty list.
   - *How tested*: Executed `test_probe_negative_limit_behavior` in [test_probe_limit.py](file:///var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/test_probe_limit.py) calling `db.search(where('v') > 0, limit=-1)` on 3 matching documents.
   - *Outcome*: **Confirmed** (Returned 2 documents because `docs[:-1]` slices off the last element. Confirmed as a minor nit).

---

## Commands Run
- `git diff edff96aeb2616402e9489d46e90a592c05565621...HEAD`: Inspected diff across codebase.
- `python -m pytest -q`: Ran entire unit test suite (240 passed in 0.78s).
- `python -m mypy tinydb tests`: Verified type annotations and signatures (Success: no issues found in 20 source files).
- `python -m pytest /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/test_probe_limit.py -v && python /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/probe_base_behavior.py && python -m pytest -q`: Executed independent test probes, verified base behavior, and re-verified full test suite.

### Findings

| ID | Severity | Category | Location | Description |
|---|---|---|---|---|
| nit-negative-limit-slicing | nit | code | `tinydb/table.py:252` | Passing a negative integer for `limit` (e.g. `limit=-1`) is not validated and gets passed directly to Python slice indexing `[:limit]`, returning all matching documents except the last N instead of returning an empty list or raising a `ValueError`. |

### Checks the reviewer ran

- `git diff edff96aeb2616402e9489d46e90a592c05565621...HEAD`: Showed additions of limit: Optional[int] = None to Table.search in tinydb/table.py, updating docstrings and applying [:limit] to cached and uncached return values, plus 12 test cases in tests/test_aut
- `python -m pytest -q`: 240 passed in 0.78s (100% pass rate across test suite).
- `python -m mypy tinydb tests`: Success: no issues found in 20 source files.
- `python -m pytest /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/test_probe_limit.py -v && python /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-bnjwbfua/probes/probe_base_behavior.py && python -m pytest -q`: 5 probe tests passed (cache isolation, JSON storage persistence/invalidation, uncacheable queries, base comparison, negative limit behavior); confirmed base table.py rejected limit; 240 unit tests pas
---
_Generated by AutoSE. A human decides whether to merge (DESIGN §13)._
