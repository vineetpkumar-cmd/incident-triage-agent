from servers.servicenow_server import get_incident
import servers.servicenow_server as servicenow_server


def test_get_existing_incident():
    result = get_incident("INC0010001")

    assert result["number"] == "INC0010001"
    assert result["short_description"] == "Email service unavailable"
    assert result["priority"] == "P1"

def test_get_existing_incident():
    result = get_incident("INC0010001")

    assert result["number"] == "INC0010001"
    assert result["short_description"] == "Email service unavailable"
    assert result["priority"] == "P1"
def test_get_missing_incident():
    result = get_incident("INC9999999")

    assert result == {
        "error": "Incident INC9999999 was not found."
    }
    import servers.servicenow_server as servicenow_server


def test_get_incident_sla_for_breached_incident():
    assert hasattr(servicenow_server, "get_incident_sla")

    result = servicenow_server.get_incident_sla("INC0010002")

    assert result == {
        "incident_number": "INC0010002",
        "priority": "P2",
        "sla_breached": True,
        "requires_escalation": True,
    }
def test_search_related_incidents():
    assert hasattr(servicenow_server, "search_related_incidents")

    result = servicenow_server.search_related_incidents(
        "INC0010001"
    )

    related_numbers = [
        incident["number"]
        for incident in result["related_incidents"]
    ]

    assert "INC0010004" in related_numbers
    assert "INC0010001" not in related_numbers