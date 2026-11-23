"""Shared fixtures. No network, no LLM, no `claude` binary: agents are FakeRunner or a stub script."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKFLOW))

from autose import config  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
#: A clean tinydb @ edff96a with a venv (override with AUTOSE_TEST_TINYDB).
TINYDB_SRC = Path(os.environ.get(
    "AUTOSE_TEST_TINYDB",
    "/private/tmp/claude-501/-Users-vishesh-College-4-1-ASE-autose-assignment3/"
    "51dce3d2-cbe4-40aa-b3ed-2007c29ee1d2/scratchpad/tinydb-up"))


@pytest.fixture(autouse=True)
def fixture_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use tiny fixture templates so tests never depend on the real prompt files."""
    monkeypatch.setattr(config, "PROMPTS_DIR", FIXTURES / "prompts")
    monkeypatch.setattr(config, "SKILL_FILE", FIXTURES / "prompts" / "SKILL.md")
    for k in list(os.environ):
        if k.startswith("AUTOSE_") and k not in ("AUTOSE_TEST_TINYDB",):
            monkeypatch.delenv(k)


@pytest.fixture(scope="session")
def tinydb_python() -> str:
    py = TINYDB_SRC / ".venv" / "bin" / "python"
    if not py.exists():
        pytest.skip(f"tinydb venv not found at {py}")
    return str(py)


@pytest.fixture
def tinydb_repo(tmp_path: Path, tinydb_python: str) -> Path:
    """A private copy of the clean tinydb checkout (the source is never modified)."""
    dest = tmp_path / "tinydb"
    shutil.copytree(TINYDB_SRC, dest, ignore=shutil.ignore_patterns(
        ".venv", ".mypy_cache", ".pytest_cache", ".coverage", "__pycache__"), symlinks=True)
    assert subprocess.run(["git", "status", "--porcelain"], cwd=dest, capture_output=True,
                          text=True).stdout.strip() == "", "tinydb source must be clean"
    return dest


@pytest.fixture
def pop_fixture(tmp_path: Path) -> Path:
    """A fresh copy of the 'add Table.pop' FakeRunner fixture (scripts are consumed)."""
    dest = tmp_path / "fx"
    shutil.copytree(FIXTURES / "pop", dest)
    return dest
