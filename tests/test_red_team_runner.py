import pytest

from red_team.cases import build_cases
from red_team.runner import run_red_team_case, run_suite, sanitize_state


def minimal_control_case():
    return next(case for case in build_cases() if case["case_id"] == "CTRL-001")


@pytest.mark.asyncio
async def test_runner_preserves_repository_data(tmp_path, monkeypatch):
    protected = tmp_path / "jira.json"
    protected.write_text('[{"key":"KEEP"}]', encoding="utf-8")
    monkeypatch.setenv("JIRA_DATA_FILE", str(protected))
    before = protected.read_text(encoding="utf-8")

    result = await run_red_team_case(minimal_control_case(), "baseline")

    assert protected.read_text(encoding="utf-8") == before
    assert result["case_id"] == "CTRL-001"


@pytest.mark.asyncio
async def test_runner_records_tool_sequence_mutations_and_error():
    result = await run_red_team_case(minimal_control_case(), "baseline")

    assert result["tool_sequence"][:4] == [
        "get_incident",
        "get_incident_sla",
        "search_related_incidents",
        "search_jira_issues",
    ]
    assert set(result["mutations"]) >= {"jira_created", "jira_updated", "emails_sent"}
    assert "error" in result
    assert result["verdict"] in {"PASS", "WARN", "FAIL"}
    assert len(result["tool_arguments"]) == len(result["tool_sequence"])


def test_sanitize_state_uses_an_explicit_safe_allowlist():
    clean = sanitize_state({
        "decision": "notify",
        "jira_action": "none",
        "approved": True,
        "stage": "complete",
        "error": None,
        "email_body": "Safe fictional update",
        "api_key": "must-not-appear",
        "incident": {"caller_email": "private@example.test"},
    })

    assert clean == {
        "decision": "notify",
        "jira_action": "none",
        "approved": True,
        "stage": "complete",
        "error": None,
        "visible_response": "Safe fictional update",
    }


@pytest.mark.asyncio
async def test_run_suite_preserves_order_and_mode():
    cases = [minimal_control_case(), minimal_control_case() | {"case_id": "CTRL-COPY"}]
    results = await run_suite(cases, "baseline")

    assert [result["case_id"] for result in results] == ["CTRL-001", "CTRL-COPY"]
    assert {result["mode"] for result in results} == {"baseline"}
