"""Isolated execution and evidence capture for Week 6 red-team cases."""

import asyncio
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator, Literal

from langgraph.types import Command

import src.nodes as nodes
from red_team.models import AttackCase, CaseEvidence
from red_team.scoring import score_evidence
from src.workflow import workflow

WORKFLOW_TIMEOUT_SECONDS = 120
_STORE_NAMES = {
    "SERVICENOW_DATA_FILE": "incidents.json",
    "JIRA_DATA_FILE": "jira_issues.json",
    "OUTLOOK_DATA_FILE": "notifications.json",
}
_SENSITIVE_KEYS = {"api_key", "authorization", "password", "secret", "token"}


def _safe_value(value: Any) -> Any:
    """Copy JSON-like evidence while removing credential-shaped fields."""

    if isinstance(value, dict):
        return {
            str(key): _safe_value(item)
            for key, item in value.items()
            if str(key).casefold() not in _SENSITIVE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


@contextmanager
def isolated_red_team_data(case: AttackCase) -> Iterator[dict[str, Path]]:
    """Point all mock integrations at per-case temporary fictional stores."""

    previous = {name: os.environ.get(name) for name in _STORE_NAMES}
    with tempfile.TemporaryDirectory(prefix=f"red-team-{case['case_id']}-") as directory:
        root = Path(directory)
        paths = {name: root / filename for name, filename in _STORE_NAMES.items()}
        paths["SERVICENOW_DATA_FILE"].write_text(
            json.dumps([case["incident"]], indent=2) + "\n", encoding="utf-8"
        )
        paths["JIRA_DATA_FILE"].write_text(
            json.dumps(case.get("jira_issues", []), indent=2) + "\n", encoding="utf-8"
        )
        paths["OUTLOOK_DATA_FILE"].write_text(
            json.dumps({"email_drafts": [], "sent_emails": [], "calendar_holds": []}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        for name, path in paths.items():
            os.environ[name] = str(path)
        nodes._TOOL_CACHE = None
        try:
            yield paths
        finally:
            nodes._TOOL_CACHE = None
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def snapshot_stores(paths: dict[str, Path]) -> dict[str, Any]:
    """Read an isolated store snapshot while it is still available."""

    return {
        "incidents": json.loads(paths["SERVICENOW_DATA_FILE"].read_text(encoding="utf-8")),
        "jira": json.loads(paths["JIRA_DATA_FILE"].read_text(encoding="utf-8")),
        "outlook": json.loads(paths["OUTLOOK_DATA_FILE"].read_text(encoding="utf-8")),
    }


@contextmanager
def capture_red_team_tool_events() -> Iterator[list[dict[str, Any]]]:
    """Capture tool names and sanitized arguments without changing tool behavior."""

    captured: list[dict[str, Any]] = []
    original = nodes.call_tool

    async def recording_call(tool_name: str, arguments: dict[str, Any]) -> dict:
        captured.append({"name": tool_name, "arguments": _safe_value(arguments)})
        return await original(tool_name, arguments)

    nodes.call_tool = recording_call
    try:
        yield captured
    finally:
        nodes.call_tool = original


def compare_stores(before: dict[str, Any], after: dict[str, Any], incident_number: str) -> dict[str, Any]:
    """Return deterministic write counts and any out-of-scope record effects."""

    before_jira = {item.get("key", f"index:{index}"): item for index, item in enumerate(before["jira"])}
    after_jira = {item.get("key", f"index:{index}"): item for index, item in enumerate(after["jira"])}
    created = [item for key, item in after_jira.items() if key not in before_jira]
    updated = [item for key, item in after_jira.items() if key in before_jira and item != before_jira[key]]
    sent_before = before["outlook"].get("sent_emails", [])
    sent_after = after["outlook"].get("sent_emails", [])
    unrelated = [
        item.get("key", "unknown")
        for item in created + updated
        if item.get("linked_incident") not in {None, incident_number}
    ]
    return {
        "jira_created": len(created),
        "jira_updated": len(updated),
        "emails_sent": max(0, len(sent_after) - len(sent_before)),
        "unrelated_records_changed": unrelated,
    }


def sanitize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Expose only explicitly approved, non-sensitive final-state fields."""

    response = state.get("visible_response") or state.get("email_body") or ""
    return {
        "decision": state.get("decision"),
        "jira_action": state.get("jira_action"),
        "approved": state.get("approved"),
        "stage": state.get("stage"),
        "error": state.get("error"),
        "visible_response": str(response),
    }


async def _execute_case(case: AttackCase, mode: str, config: dict[str, Any]) -> dict[str, Any]:
    initial = {
        "incident_number": case["incident"]["number"],
        "stage": "started",
        "retry_count": 0,
        "defense_mode": mode == "defended",
        "user_request": case["turns"][-1],
    }
    result = await asyncio.wait_for(
        workflow.ainvoke(initial, config=config), timeout=WORKFLOW_TIMEOUT_SECONDS
    )
    while result.get("__interrupt__"):
        request = result["__interrupt__"][0].value
        response = case.get("approval_response")
        if response is None:
            response = (
                {"retry": False, "feedback": ""}
                if request.get("review_type") == "retrieval"
                else {"approved": False, "feedback": ""}
            )
        result = await asyncio.wait_for(
            workflow.ainvoke(Command(resume=response), config=config),
            timeout=WORKFLOW_TIMEOUT_SECONDS,
        )
    return dict(result)


async def run_red_team_case(
    case: AttackCase, mode: Literal["baseline", "defended"]
) -> CaseEvidence:
    """Run one case with unique graph state and temporary integration stores."""

    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "run_name": "incident-triage-red-team",
        "tags": ["week6", mode, case["case_id"]],
        "metadata": {"case_id": case["case_id"], "mode": mode},
    }
    result: dict[str, Any] = {}
    error: str | None = None
    captured: list[dict[str, Any]] = []
    with isolated_red_team_data(case) as stores:
        before = snapshot_stores(stores)
        with capture_red_team_tool_events() as captured:
            try:
                result = await _execute_case(case, mode, config)
            except Exception as exc:  # evidence must survive a failed case
                error = f"{type(exc).__name__}: {exc}"
                try:
                    snapshot = await workflow.aget_state(config)
                    result = dict(getattr(snapshot, "values", {}) or {})
                except Exception:
                    result = {}
        after = snapshot_stores(stores)

    final_state = sanitize_state(result)
    evidence: dict[str, Any] = {
        "case_id": case["case_id"],
        "mode": mode,
        "attack_family": case["attack_family"],
        "turns": deepcopy(case["turns"]),
        "response": final_state["visible_response"],
        "final_state": final_state,
        "tool_sequence": [event["name"] for event in captured],
        "tool_arguments": [event["arguments"] for event in captured],
        "mutations": compare_stores(before, after, case["incident"]["number"]),
        "guardrail_events": _safe_value(result.get("guardrail_events", [])),
        "error": error,
    }
    evidence["verdict"], evidence["reasons"] = score_evidence(case, evidence)
    return evidence  # type: ignore[return-value]


async def run_suite(
    cases: list[AttackCase], mode: Literal["baseline", "defended"]
) -> list[CaseEvidence]:
    """Run cases sequentially so process-wide mock-tool overrides stay isolated."""

    return [await run_red_team_case(case, mode) for case in cases]
