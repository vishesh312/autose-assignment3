#!/usr/bin/env python3
"""Score an implementation worktree against the hidden tests (E2 and the pipeline runs).

usage: score.py <issue N> <worktree with the change> <clean base repo> <python of tinydb venv>

Prints JSON:
  hidden_passed / hidden_total: hidden acceptance tests that pass on the change.
  gen_tests: number of tests in tests/test_autose_issue_N.py.
  gen_fail_on_reference: generated tests that FAIL when run against the reference fix. Each one
    is evidence of test-implementation collusion: the test encodes behaviour the reference
    contradicts (experiment/variants.md, E2).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def pytest_counts(py: str, cwd: Path, target: str) -> tuple[int, int, str]:
    p = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:randomly", target],
                       cwd=cwd, capture_output=True, text=True, timeout=600)
    tail = (p.stdout + p.stderr)[-3000:]
    passed = sum(int(x) for x in re.findall(r"(\d+) passed", tail))
    failed = sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", tail))
    return passed, passed + failed, tail


def main() -> None:
    n, wt, base, py = int(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), sys.argv[4]
    hidden = HERE / "hidden_tests" / f"test_issue_{n}.py"
    out: dict[str, object] = {"issue": n, "worktree": str(wt)}
    dest = wt / "tests" / f"_hidden_issue_{n}.py"
    shutil.copyfile(hidden, dest)
    try:
        hp, ht, tail = pytest_counts(py, wt, str(dest.relative_to(wt)))
        out.update(hidden_passed=hp, hidden_total=ht)
        if ht == 0:
            out["hidden_tail"] = tail[-800:]
    finally:
        dest.unlink(missing_ok=True)
    gen = wt / "tests" / f"test_autose_issue_{n}.py"
    if gen.exists():
        tmp = Path(tempfile.mkdtemp(prefix="score-ref-")) / "ref"
        subprocess.run(["git", "-C", str(base), "worktree", "add", "-q", "--detach", str(tmp), "HEAD"], check=True)
        try:
            subprocess.run(["git", "apply", str(HERE / "hidden_tests" / "reference" / f"issue-{n}.patch")],
                           cwd=tmp, check=True)
            shutil.copyfile(gen, tmp / "tests" / gen.name)
            gp, gt, _ = pytest_counts(py, tmp, f"tests/{gen.name}")
            out.update(gen_tests=gt, gen_fail_on_reference=gt - gp)
        finally:
            subprocess.run(["git", "-C", str(base), "worktree", "remove", "--force", str(tmp)], check=False)
    else:
        out.update(gen_tests=0, gen_fail_on_reference=None)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
