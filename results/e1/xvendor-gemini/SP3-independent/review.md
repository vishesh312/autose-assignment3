## AutoSE review (round 1): **REQUEST_CHANGES**

> Verification pass on blocking findings: 1 confirmed.

The pull request attempts to fix cross-field fragment query cache poisoning by adding an AST walk (_is_fragment_query) in Table.search that completely bypasses the query cache. However, this is an incorrect approach working at the wrong layer: the root cause is that Query.fragment in tinydb/queries.py omits self._path from its hash tuple, causing queries targeting different field paths to compare equal (q_home == q_work is True) and collide in sets/dicts. Furthermore, this change unnecessarily disables query caching for all fragment queries and compound queries containing them. The fix should be made in tinydb/queries.py by including self._path in Query.fragment's hash tuple.

## Verdict: Changes Requested

### Summary
The pull request attempts to resolve cross-field fragment query cache poisoning by introducing an AST walk (`_is_fragment_query`) in [tinydb/table.py](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/pr/tinydb/table.py#L265) that completely bypasses `Table._query_cache` for fragment queries. This approach works at the wrong architectural layer and violates TinyDB's query design constraints: `Query.fragment` in [tinydb/queries.py](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/pr/tinydb/queries.py#L489) omits `self._path` from its hash tuple, leaving queries on different fields equal (`q_home == q_work` is `True`) and causing hash collisions. Furthermore, bypassing `_query_cache` permanently destroys query caching benefits for all fragment queries and compound queries containing them. The fix should be implemented directly in `tinydb/queries.py` by including `self._path` in `Query.fragment`'s hash tuple.

---

### Important Findings

#### 1. [`approach`] Wrong layer: Query cache bypassed in `Table.search` instead of fixing query hash in `Query.fragment`
- **File**: [tinydb/table.py:265](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/pr/tinydb/table.py#L265)
- **Problem**: Rather than ensuring `Query.fragment` includes `self._path` in its query hash tuple (as every other query method in `Query` does), the PR adds a recursive traversal `_is_fragment_query` in `Table.search` that bypasses the query cache.
- **Consequences**:
  1. `Query().home.fragment({'city': 'Paris'}) == Query().work.fragment({'city': 'Paris'})` still evaluates to `True`, failing to fix the query equality bug explicitly reported in issue #2.
  2. `hash(Query().home.fragment(...)) == hash(Query().work.fragment(...))`, causing query collisions in sets, dictionaries, or custom cache structures.
  3. `Table._query_cache` is completely disabled for all fragment queries and compound queries (`&`, `|`, `~`) containing fragment queries, hurting performance on repeated queries.
  4. It violates TinyDB's query design constraint that `_hash` must contain every semantic parameter of the query.
- **Evidence**:
  Running `/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/probe_fragment_issues.py`:
  ```
  q_home._hash: ('fragment', {'city': 'Paris'})
  q_work._hash: ('fragment', {'city': 'Paris'})
  q_home == q_work: True
  hash(q_home) == hash(q_work): True
  len({q_home, q_work}): 1
  Cache size after search: 0
  Query in cache: False
  ```
  Running pytest probe `/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/test_probe_fragment.py`:
  ```
  FAILED test_fragment_query_equality: assert QueryImpl('fragment', {'city': 'Paris'}) != QueryImpl('fragment', {'city': 'Paris'})
  FAILED test_fragment_query_hash: assert hash(q_home) != hash(q_work)
  FAILED test_fragment_queries_are_cached: assert q in table._query_cache
  ```
- **Suggested Fix**:
  Revert changes to [tinydb/table.py](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/pr/tinydb/table.py). In [tinydb/queries.py](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/pr/tinydb/queries.py#L489-L501), include `self._path` in the hash tuple:
  ```python
  def fragment(self, document: Mapping) -> QueryInstance:
      def test(value):
          for key in document:
              if key not in value or value[key] != document[key]:
                  return False
          return True

      return self._generate_test(
          lambda value: test(value),
          ('fragment', self._path, freeze(document)),
          allow_empty_path=True
      )
  ```

---

### Pre-existing Findings
*None.*

---

### Nits

#### 1. [`tests`] Missing test assertions for query equality, hash uniqueness, and cache storage
- **File**: [tests/test_autose_issue_2.py:1](file:///private/var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/pr/tests/test_autose_issue_2.py#L1)
- **Problem**: The tests only test query evaluation outputs under the bypass, but do not assert `q_home != q_work`, hash distinctness, or that fragment queries are correctly stored in `_query_cache`.
- **Suggested Fix**: Add unit tests in `tests/test_queries.py` verifying that queries targeting different field paths do not compare equal and that `_query_cache` properly caches query results.

---

### Hypotheses Tested

| Hypothesis | How Tested | Outcome |
| :--- | :--- | :--- |
| `fragment()` queries on different fields still compare equal and have identical hashes | Ran probe `probe_fragment_issues.py` and `test_probe_fragment.py` asserting `q_home != q_work` | **Confirmed** (`q_home == q_work` is `True`) |
| Query caching is completely disabled for all `fragment()` queries | Inspected `table._query_cache` size after `db.search()` in `probe_fragment_issues.py` | **Confirmed** (cache size is 0) |
| Fixing `Query.fragment` hash tuple in `tinydb/queries.py` solves equality, caching, and passes all tests | Ran `probe_caching_proper_fix.py` and `test_probe_proper_fix_against_pr_tests.py` | **Confirmed** (clean cache separation, all tests pass) |
| PR tests in `tests/test_autose_issue_2.py` pass even though equality and hashing remain broken | Ran `python -m pytest tests/test_autose_issue_2.py -q` | **Confirmed** (5 passed in 0.13s) |

---

### Commands Run
- `python -m pytest -q` (`233 passed in 0.76s`)
- `python /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/probe_fragment_issues.py` (Confirmed hash collision, equality `True`, cache size 0)
- `python -m pytest /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/test_probe_fragment.py -q` (3 failed in 0.03s)
- `python /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/probe_caching_proper_fix.py` (Confirmed cache holds distinct entries without collision)
- `python -m pytest /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/test_probe_proper_fix_against_pr_tests.py -q` (6 passed in 0.01s)
- `python -m pytest tests/test_autose_issue_2.py -q` (5 passed in 0.13s)

### Findings

| ID | Severity | Category | Location | Description |
|---|---|---|---|---|
| approach-wrong-layer-fragment-cache-bypass | important (confirmed) | approach | `tinydb/table.py:265` | The PR attempts to fix cross-field cache poisoning at the wrong architectural layer by hacking Table.search to bypass the query cache (_is_fragment_query) instead of fixing the root cause in Query.fragment in tinydb/queries.py. By not including self._path in Query.fragment's hash tuple: (1) Query().home.fragment({'city': 'Paris'}) == Query().work.fragment({'city': 'Paris'}) continues to evaluate to True, leaving queries on different fields incorrectly equal; (2) hash(Query().home.fragment(...)) == hash(Query().work.fragment(...)), causing hash collisions in sets, dicts, or other caching layers; (3) query caching is entirely disabled for all fragment queries and any compound query (&, \|, ~) containing a fragment query; and (4) it violates TinyDB's query design constraint that _hash must include every semantic parameter of the query. |
| tests-missing-equality-and-cache-coverage | nit | tests | `tests/test_autose_issue_2.py:1` | The new test suite in tests/test_autose_issue_2.py only asserts search/count/get results under the Table.search cache bypass, omitting tests for query equality (Query().home.fragment(...) != Query().work.fragment(...)), distinct query hashes, and verification that fragment queries are properly populated into Table._query_cache. |

### Checks the reviewer ran

- `python -m pytest -q`: 233 passed in 0.76s
- `python /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/probe_fragment_issues.py`: q_home._hash: ('fragment', {'city': 'Paris'}) q_work._hash: ('fragment', {'city': 'Paris'}) q_root._hash: ('fragment', {'city': 'Paris'}) q_home == q_work: True hash(q_home) == hash(q_work): True len(
- `python -m pytest /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/test_probe_fragment.py -q`: FAILED test_fragment_query_equality - AssertionError: Queries on different fields should not be equal! Both hashes are ('fragment', {'city': 'Paris'}) FAILED test_fragment_query_hash - AssertionError:
- `python /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/probe_caching_proper_fix.py`: Success: query cache has 2 entries without collision! Entries in cache: [QueryImpl('fragment', ('home',), {'city': 'Paris'}), QueryImpl('fragment', ('work',), {'city': 'Paris'})]
- `python -m pytest /var/folders/3q/2m8v425s7p39t7qxjp0kcdw80000gn/T/autose-review-ybq9hlv5/probes/test_probe_proper_fix_against_pr_tests.py -q`: 6 passed in 0.01s
- `python -m pytest tests/test_autose_issue_2.py -q`: 5 passed in 0.13s
---
_Generated by AutoSE. A human decides whether to merge (DESIGN §13)._
