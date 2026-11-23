"""Static invariants of the workflow files (DESIGN §6 permissions, §10.1, §11; ADR-008 independence)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")
WF = Path(__file__).resolve().parents[1] / "github-workflows"


def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((WF / name).read_text())


def test_workflow_level_permissions_are_empty() -> None:
    for name in ("autose.yml", "autose-round.yml", "ci.yml"):
        assert load(name)["permissions"] == {}, name


def test_job_permissions_match_design() -> None:
    jobs = load("autose.yml")["jobs"]
    assert jobs["gate"]["permissions"] == {"issues": "write", "pull-requests": "read", "contents": "read"}
    assert jobs["build"]["permissions"] == {"contents": "write", "pull-requests": "write", "issues": "write"}
    assert jobs["finalize"]["permissions"] == {"issues": "write", "pull-requests": "write"}
    assert jobs["finalize"]["if"].startswith("always()")
    rjobs = load("autose-round.yml")["jobs"]
    assert rjobs["review"]["permissions"] == {"contents": "read", "issues": "read", "pull-requests": "read"}
    assert rjobs["post"]["permissions"] == {"pull-requests": "write", "issues": "write"}
    assert rjobs["ci"]["permissions"] == {"contents": "read", "statuses": "write"}


def test_review_job_is_isolated() -> None:
    steps = load("autose-round.yml")["jobs"]["review"]["steps"]
    downloads = [s for s in steps if str(s.get("uses", "")).startswith("actions/download-artifact")]
    assert len(downloads) == 1 and "review-r${{ inputs.prev_round }}" in downloads[0]["with"]["name"]
    for s in steps:
        if str(s.get("uses", "")).startswith("actions/checkout"):
            assert s["with"]["persist-credentials"] is False
    agent = next(s for s in steps if s.get("name", "").startswith("Independent review"))
    assert "GH_TOKEN" not in agent["env"] and "GITHUB_TOKEN" not in agent["env"]
    assert "--no-github" in agent["run"]


def test_secrets_only_in_agent_steps_and_cli_pinned() -> None:
    text = (WF / "autose.yml").read_text() + (WF / "autose-round.yml").read_text()
    assert "claude-code@2.1.331" in text and "npm install -g @anthropic-ai/claude-code\n" not in text
    for name in ("autose.yml", "autose-round.yml"):
        for job_name, job in load(name)["jobs"].items():
            assert "ANTHROPIC_API_KEY" not in str(job.get("env", {})), job_name
            for s in job.get("steps", []):
                if "ANTHROPIC_API_KEY" in str(s.get("env", {})):
                    assert "python -m autose" in s["run"], (job_name, s.get("name"))


def test_concurrency_groups() -> None:
    wf = load("autose.yml")
    assert "autose-noop-" in wf["concurrency"]["group"] and wf["concurrency"]["cancel-in-progress"] is False
    for job in ("build", "round1", "round2", "round3"):
        assert wf["jobs"][job]["concurrency"]["group"] == "autose-canonical-${{ needs.gate.outputs.issue }}"
    assert wf["jobs"]["round3"]["with"]["final"] is True
