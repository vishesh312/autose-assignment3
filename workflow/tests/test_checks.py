"""Deterministic checks (DESIGN §2, §8; ADR-005 path allowlists; ADR-007)."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from autose import checks, config

FX = Path(__file__).parent / "fixtures" / "pop"


def load(name: str) -> dict:
    return json.loads((FX / name).read_text())


# ---------------------------------------------------------------- globs / allowlists

@pytest.mark.parametrize("path,pattern,ok", [
    ("tinydb/table.py", "tinydb/**", True),
    ("tinydb/sub/x.py", "tinydb/**", True),
    ("tests/conftest.py", "**/conftest.py", True),
    ("conftest.py", "**/conftest.py", True),
    ("setup.py", "setup.py", True),
    ("tinydb.py", "tinydb/**", False),
    ("tests/test_x.py", "tests/*.py", True),
    ("tests/a/test_x.py", "tests/*.py", False),
])
def test_glob_match(path: str, pattern: str, ok: bool) -> None:
    assert checks.glob_match(path, pattern) is ok


def test_path_violations_developer_and_tester() -> None:
    dev = [config.package_glob()]
    assert checks.path_violations(["tinydb/table.py"], dev) == []
    assert checks.path_violations(["tinydb/table.py", "tests/test_tables.py", ".github/workflows/x.yml",
                                   "pyproject.toml"], dev) == [".github/workflows/x.yml", "pyproject.toml",
                                                                "tests/test_tables.py"]
    tester = [config.tester_file(7)]
    assert checks.path_violations(["tests/test_autose_issue_7.py"], tester) == []
    assert checks.path_violations(["tests/conftest.py", "tinydb/table.py"], tester + ["tests/**"]) == \
        ["tests/conftest.py", "tinydb/table.py"]


# ---------------------------------------------------------------- AST symbol lookup

SRC = '''
from typing import TYPE_CHECKING
X: int = 1
Y = 2
def top(): ...
class Table:
    default_table_name = "_default"
    def insert(self): ...
    class Inner:
        def deep(self): ...
if TYPE_CHECKING:
    def typed_only(): ...
'''


@pytest.mark.parametrize("symbol,found", [
    ("top", True), ("Table", True), ("Table.insert", True), ("Table.default_table_name", True),
    ("Table.Inner.deep", True), ("X", True), ("Y", True), ("typed_only", True),
    ("Table.nope", False), ("nope", False), ("top.inner", False), ("Table.insert.x", False),
])
def test_find_symbol(symbol: str, found: bool) -> None:
    assert checks.find_symbol(SRC, symbol) is found


def test_check_design_on_tinydb(tinydb_repo: Path) -> None:
    spec, design = load("spec.json"), load("design.json")
    assert checks.check_design(design, spec, tinydb_repo).passed
    bad = copy.deepcopy(design)
    bad["changes"][0]["symbol"] = "Table.invented_method"
    r = checks.check_design(bad, spec, tinydb_repo)
    assert not r.passed and "invented_method" in r.reason
    bad = copy.deepcopy(design)
    bad["changes"].append({"path": "tests/test_x.py", "symbol": "", "kind": "new", "new_file": True,
                           "description": "", "acs": []})
    assert "only tinydb/**" in checks.check_design(bad, spec, tinydb_repo).reason
    bad = copy.deepcopy(design)
    bad["changes"][0]["acs"] = ["AC-1"]
    assert "AC-2 is not covered" in checks.check_design(bad, spec, tinydb_repo).reason
    bad = copy.deepcopy(design)
    bad["changes"][0]["path"] = "tinydb/ghost.py"
    assert "does not exist" in checks.check_design(bad, spec, tinydb_repo).reason
    bad["changes"][0].update(kind="new", new_file=True)
    assert checks.check_design(bad, spec, tinydb_repo).passed


# ---------------------------------------------------------------- S1

def test_check_spec_and_judge() -> None:
    spec = load("spec.json")
    assert checks.check_spec(spec).passed and not checks.blocking_questions(spec)
    bad = copy.deepcopy(spec)
    bad["acceptance_criteria"][0]["observable"] = " "
    bad["acceptance_criteria"][1]["requirement"] = "REQ-9"
    r = checks.check_spec(bad)
    assert "empty 'observable'" in r.reason and "REQ-9" in r.reason
    assert not checks.check_spec({**spec, "acceptance_criteria": []}).passed
    judge = load("judge.json")
    assert checks.check_judge(judge, spec).passed
    judge["verdicts"] = judge["verdicts"][:1]
    assert "AC-2: the judge gave no verdict" in checks.check_judge(judge, spec).reason


# ---------------------------------------------------------------- snapshots / touched / restore

def test_snapshot_touched_restore(tinydb_repo: Path) -> None:
    base = checks.git(tinydb_repo, "rev-parse", "HEAD").strip()
    (tinydb_repo / "tests" / "test_autose_issue_1.py").write_text("x = 1\n")  # pre-existing tester file
    before = checks.snapshot(tinydb_repo, base)
    (tinydb_repo / "tinydb" / "table.py").write_text("# changed\n")
    (tinydb_repo / "tinydb" / "new.py").write_text("y = 2\n")
    (tinydb_repo / "tests" / "test_autose_issue_1.py").write_text("x = 2\n")
    (tinydb_repo / "pyproject.toml").unlink()
    (tinydb_repo / "tinydb" / "__pycache__").mkdir(exist_ok=True)
    after = checks.snapshot(tinydb_repo, base)
    changed = checks.touched(before, after)
    assert changed == ["pyproject.toml", "tests/test_autose_issue_1.py", "tinydb/new.py", "tinydb/table.py"]
    bad = checks.path_violations(changed, [config.package_glob()])
    checks.restore(tinydb_repo, base, bad, before)
    assert (tinydb_repo / "pyproject.toml").exists()
    assert (tinydb_repo / "tests" / "test_autose_issue_1.py").read_text() == "x = 1\n"  # back to pre-agent state
    assert (tinydb_repo / "tinydb" / "table.py").read_text() == "# changed\n"           # allowed edit kept
    checks.reset_to_base(tinydb_repo, base)
    assert checks.dirty_paths(tinydb_repo, base) == []


def test_patch_includes_untracked(tinydb_repo: Path) -> None:
    base = checks.git(tinydb_repo, "rev-parse", "HEAD").strip()
    (tinydb_repo / "tinydb" / "extra.py").write_text("z = 3\n")
    text = checks.patch(tinydb_repo, base, ["tinydb"])
    assert "tinydb/extra.py" in text and "+z = 3" in text


# ---------------------------------------------------------------- S3/S4 against real tinydb

def _apply(repo: Path, name: str) -> None:
    subprocess.run(["git", "apply", str(FX / name)], cwd=repo, check=True)


def test_build_collect_suite_and_fails_on_base(tinydb_repo: Path, tinydb_python: str) -> None:
    base = checks.git(tinydb_repo, "rev-parse", "HEAD").strip()
    _apply(tinydb_repo, "impl_full.patch")
    assert checks.check_build(tinydb_repo, tinydb_python).passed
    test_file = config.tester_file(42)
    shutil.copyfile(FX / "issue42_tests.py.txt", tinydb_repo / test_file)
    collected, _ = checks.collect_tests(tinydb_repo, tinydb_python, test_file)
    assert len(collected) == 2
    assert checks.check_test_map(load("test_map.json"), load("spec.json"), collected, test_file).passed
    suite = checks.run_suite(tinydb_repo, tinydb_python)
    assert suite.passed and suite.counts["tests"] >= 230
    assert checks.check_types(tinydb_repo, tinydb_python).passed
    fob = checks.fails_on_base(tinydb_repo, base, test_file, tinydb_python)
    assert fob.passed, fob.reason
    assert checks.git(tinydb_repo, "worktree", "list").count("\n") == 1  # temp worktree removed
    # vacuous tests pass on base -> the anti-vacuous check fails
    shutil.copyfile(FX / "vacuous_tests.py.txt", tinydb_repo / test_file)
    fob = checks.fails_on_base(tinydb_repo, base, test_file, tinydb_python)
    assert not fob.passed and "no new test fails" in fob.reason


def test_build_fails_on_type_error(tinydb_repo: Path, tinydb_python: str) -> None:
    p = tinydb_repo / "tinydb" / "utils.py"
    p.write_text(p.read_text() + "\n\ndef bad() -> int:\n    return 'x'\n")
    r = checks.check_build(tinydb_repo, tinydb_python)
    assert not r.passed and "mypy" in r.reason


def test_suite_reports_failing_ids(tinydb_repo: Path, tinydb_python: str) -> None:
    _apply(tinydb_repo, "impl_buggy.patch")
    shutil.copyfile(FX / "issue42_tests.py.txt", tinydb_repo / config.tester_file(42))
    suite = checks.run_suite(tinydb_repo, tinydb_python)
    assert not suite.passed
    assert suite.failing == ["tests/test_autose_issue_42.py::test_ac2_pop_missing_id_raises_keyerror"]


# ---------------------------------------------------------------- S6 validity and routing

def _review(verdict: str, findings: list[dict], checks_performed: list[dict] | None = None) -> dict:
    r = load("review_ok.json")
    r.update(verdict=verdict, findings=findings)
    if checks_performed is not None:
        r["checks_performed"] = checks_performed
    return r


def _finding(sev: str, cat: str, evidence: str = "ran it") -> dict:
    return {"id": "F-1", "severity": sev, "category": cat, "file": "tinydb/table.py", "line": 3,
            "description": "d", "evidence": evidence, "suggested_fix": "s"}


def test_review_problems() -> None:
    assert checks.review_problems(_review("approve", [])) == []
    assert "approve requires" in checks.review_problems(_review("approve", [], []))[0]
    assert "must not carry blocking" in checks.review_problems(_review("approve", [_finding("blocking", "code")]))[0]
    assert checks.review_problems(_review("approve", [_finding("minor", "code")])) == []
    assert "requires at least one blocking" in checks.review_problems(
        _review("changes_requested", [_finding("minor", "code")]))[0]
    assert "no evidence" in checks.review_problems(_review("changes_requested",
                                                           [_finding("blocking", "code", " ")]))[0]


@pytest.mark.parametrize("cats,route", [
    ([("blocking", "code"), ("blocking", "approach")], "S2"),
    ([("blocking", "code"), ("blocking", "tests")], "S3"),
    ([("blocking", "tests")], "S4"),
    ([("minor", "approach"), ("blocking", "tests")], "S4"),   # only blocking findings route
])
def test_review_route(cats: list[tuple[str, str]], route: str) -> None:
    assert checks.review_route(_review("changes_requested", [_finding(s, c) for s, c in cats])) == route
    assert checks.review_route(_review("approve", [])) is None
