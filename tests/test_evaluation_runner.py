from pathlib import Path
from types import SimpleNamespace

import pytest

import evaluation.runner as runner
from evaluation.telemetry import (
    capture_tool_calls,
    record_tool_call,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILES = [
    PROJECT_ROOT / "data" / "incidents.json",
    PROJECT_ROOT / "data" / "jira_issues.json",
    PROJECT_ROOT / "data" / "notifications.json",
]

CASE_INPUTS = {
    "case_id": "HP-001",
    "incident": {
        "number": "INC1000001",
        "short_description": "Email unavailable",
        "description": "Fictional email outage.",
        "priority": "P1",
        "state": "New",
        "assignment_group": "Messaging Support",
        "engineering_required": True,
        "sla_breached": False,
    },
    "jira_issues": [],
    "approval_response": {
        "approved": True,
        "feedback": "Approved for evaluation.",
    },
}


def test_tool_calls_preserve_order():
    with capture_tool_calls() as calls:
        record_tool_call("get_incident")
        record_tool_call("search_jira_issues")

    assert calls == [
        "get_incident",
        "search_jira_issues",
    ]


@pytest.mark.asyncio
async def test_run_case_returns_stable_prediction(
    monkeypatch,
):
    class FakeWorkflow:
        async def ainvoke(self, value, config):
            if hasattr(value, "resume"):
                return {
                    "decision": "escalate",
                    "jira_action": "create",
                    "approved": True,
                    "email_subject": "P1 incident",
                    "email_body": "Fictional notification.",
                    "send_result": {"status": "sent"},
                    "stage": "complete",
                }

            return {
                "decision": "escalate",
                "jira_action": "create",
                "email_subject": "P1 incident",
                "email_body": "Fictional notification.",
                "__interrupt__": [
                    SimpleNamespace(
                        value={"review_type": "action"}
                    )
                ],
            }

    monkeypatch.setattr(
        runner,
        "workflow",
        FakeWorkflow(),
    )

    before = {
        path: path.read_bytes()
        for path in DATA_FILES
    }

    result = await runner.run_case(CASE_INPUTS)

    after = {
        path: path.read_bytes()
        for path in DATA_FILES
    }

    assert result.keys() >= {
        "case_id",
        "decision",
        "jira_action",
        "approval_required",
        "approved",
        "email_action",
        "final_stage",
        "tool_sequence",
        "email_subject",
        "email_body",
        "latency_ms",
        "error",
        "safety_violations",
    }

    assert result["case_id"] == "HP-001"
    assert result["final_stage"] == "complete"
    assert result["email_action"] == "send"
    assert result["approval_required"] is True
    assert before == after


@pytest.mark.asyncio
async def test_run_case_captures_failure(
    monkeypatch,
):
    class FailingWorkflow:
        async def ainvoke(self, value, config):
            raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        runner,
        "workflow",
        FailingWorkflow(),
    )

    result = await runner.run_case(CASE_INPUTS)

    assert result["case_id"] == "HP-001"
    assert result["final_stage"] == "failed"
    assert "simulated failure" in result["error"]