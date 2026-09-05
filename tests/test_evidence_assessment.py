import pytest

from src.nodes import assess_evidence


COMPLETE_STATE = {
    "incident_number": "INC0010001",
    "incident": {
        "number": "INC0010001",
        "short_description": "Email unavailable",
        "description": "Employees cannot send email.",
        "priority": "P1",
        "state": "New",
        "assignment_group": "Messaging Support",
        "engineering_required": True,
    },
    "sla": {
        "incident_number": "INC0010001",
        "sla_breached": False,
    },
    "related_incidents": {
        "incident_number": "INC0010001",
        "related_incidents": [],
        "total": 0,
    },
    "jira_search": {
        "incident_number": "INC0010001",
        "issues": [],
        "total": 0,
    },
}


@pytest.mark.asyncio
async def test_complete_evidence_is_sufficient():
    result = await assess_evidence(COMPLETE_STATE)

    assert result["evidence_status"] == "sufficient"
    assert result["missing_evidence"] == []
    assert result["stage"] == "evidence_assessed"


@pytest.mark.asyncio
async def test_missing_jira_evidence_is_insufficient():
    incomplete_state = {
        **COMPLETE_STATE,
        "jira_search": {
            "incident_number": "INC0010001",
            "issues": [],
        },
    }

    result = await assess_evidence(incomplete_state)

    assert result["evidence_status"] == "insufficient"
    assert "jira_search.total" in result["missing_evidence"]


@pytest.mark.asyncio
async def test_malformed_incident_is_insufficient():
    incomplete_state = {
        **COMPLETE_STATE,
        "incident": {
            "number": "INC0010001",
            "priority": "P1",
        },
    }

    result = await assess_evidence(incomplete_state)

    assert result["evidence_status"] == "insufficient"
    assert "incident.description" in result["missing_evidence"]