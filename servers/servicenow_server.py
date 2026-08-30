
import json
import re
from pathlib import Path
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Mock ServiceNow")


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "incidents.json"
)
def extract_keywords(text: str) -> set[str]:
    """Extract meaningful lowercase words for matching."""
    words = re.findall(r"[a-zA-Z]+", text.lower())

    ignored_words = {
        "about",
        "being",
        "cannot",
        "employees",
        "incident",
        "other",
        "report",
        "reported",
        "their",
        "there",
        "these",
        "with",
    }

    return {
        word
        for word in words
        if len(word) >= 5 and word not in ignored_words
    }

def load_incidents() -> list[dict]:
    """Load fictional ServiceNow incidents from the JSON file."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


@mcp.tool()
def get_incident(incident_number: str) -> dict:
    """Retrieve one fictional ServiceNow incident by number."""
    incidents = load_incidents()
    requested_number = incident_number.strip().upper()

    for incident in incidents:
        if incident["number"] == requested_number:
            return incident

    return {
    "error": f"Incident {requested_number} was not found."
}
@mcp.tool()
def get_incident_sla(incident_number: str) -> dict:
    """Return SLA and escalation information for an incident."""
    incident = get_incident(incident_number)

    if "error" in incident:
        return incident

    priority = incident["priority"]
    sla_breached = incident["sla_breached"]

    requires_escalation = (
        priority in {"P1", "P2"} or sla_breached
    )

    return {
        "incident_number": incident["number"],
        "priority": priority,
        "sla_breached": sla_breached,
        "requires_escalation": requires_escalation,
    }
@mcp.tool()
def search_related_incidents(incident_number: str) -> dict:
    """Find incidents with the same group or shared keywords."""
    source_incident = get_incident(incident_number)

    if "error" in source_incident:
        return source_incident

    source_text = (
        f"{source_incident['short_description']} "
        f"{source_incident['description']}"
    )
    source_keywords = extract_keywords(source_text)

    related_incidents = []

    for candidate in load_incidents():
        if candidate["number"] == source_incident["number"]:
            continue

        candidate_text = (
            f"{candidate['short_description']} "
            f"{candidate['description']}"
        )
        candidate_keywords = extract_keywords(candidate_text)

        same_group = (
            candidate["assignment_group"]
            == source_incident["assignment_group"]
        )
        shared_keywords = sorted(
            source_keywords.intersection(candidate_keywords)
        )

        if same_group or shared_keywords:
            reasons = []

            if same_group:
                reasons.append("same assignment group")

            if shared_keywords:
                reasons.append(
                    f"shared keywords: {', '.join(shared_keywords)}"
                )

            related_incidents.append(
                {
                    "number": candidate["number"],
                    "short_description": candidate[
                        "short_description"
                    ],
                    "priority": candidate["priority"],
                    "state": candidate["state"],
                    "match_reason": "; ".join(reasons),
                }
            )

    return {
        "incident_number": source_incident["number"],
        "related_incidents": related_incidents,
        "total": len(related_incidents),
    }

if __name__ == "__main__":
    mcp.run()