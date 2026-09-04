import json
import os
import re
from pathlib import Path


from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Mock Jira")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = Path(
    os.getenv(
        "JIRA_DATA_FILE",
        str(PROJECT_ROOT / "data" / "jira_issues.json"),
    )
)


def load_jira_issues() -> list[dict]:
    """Load fictional Jira issues from the JSON file."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

def save_jira_issues(issues: list[dict]) -> None:
    """Save fictional Jira issues to the JSON file."""
    DATA_FILE.write_text(
        json.dumps(issues, indent=2),
        encoding="utf-8",
    )

@mcp.tool()
def search_jira_issues(incident_number: str) -> dict:
    """Find Jira issues linked to a ServiceNow incident."""
    requested_number = incident_number.strip().upper()

    matching_issues = [
        issue
        for issue in load_jira_issues()
        if issue["linked_incident"] == requested_number
    ]

    return {
        "incident_number": requested_number,
        "issues": matching_issues,
        "total": len(matching_issues),
    }

@mcp.tool()
def create_jira_issue(
    project: str,
    issue_type: str,
    summary: str,
    description: str,
    jira_priority: str,
    linked_incident: str,
    incident_priority: str,
    approved: bool = False,
) -> dict:
    """Create a fictional Jira issue with safety checks."""
    project = project.strip().upper()
    issue_type = issue_type.strip().title()
    linked_incident = linked_incident.strip().upper()
    incident_priority = incident_priority.strip().upper()

    if not re.fullmatch(r"INC\d{7}", linked_incident):
        return {
          "status": "blocked",
          "reason": (
            "Linked incident must match INC followed by "
            "seven digits."
         ),
        }

    allowed_projects = {"ENG", "OPS"}
    allowed_issue_types = {"Story", "Task", "Bug"}

    if not re.fullmatch(r"INC\d{7}", linked_incident):
        return {
            "status": "blocked",
            "reason": (
            "Linked incident must match INC followed by "
            "seven digits."
            ),
    }

    if project not in allowed_projects:
        return {
            "status": "blocked",
            "reason": f"Project {project} is not allowed.",
        }

    if issue_type not in allowed_issue_types:
        return {
            "status": "blocked",
            "reason": f"Issue type {issue_type} is not allowed.",
        }

    if incident_priority in {"P1", "P2"} and not approved:
        return {
            "status": "approval_required",
            "reason": (
                f"{incident_priority} incidents require "
                "human approval."
            ),
        }

    issues = load_jira_issues()

    for issue in issues:
        if issue["linked_incident"] == linked_incident:
            return {
                "status": "blocked",
                "reason": "A linked Jira issue already exists.",
                "existing_issue": issue["key"],
            }

    project_numbers = []

    for issue in issues:
        if issue["project"] != project:
            continue

        number_text = issue["key"].split("-")[-1]

        if number_text.isdigit():
            project_numbers.append(int(number_text))

    next_number = max(project_numbers, default=100) + 1
    issue_key = f"{project}-{next_number}"

    new_issue = {
        "key": issue_key,
        "project": project,
        "issue_type": issue_type,
        "summary": summary.strip(),
        "description": description.strip(),
        "status": "Open",
        "priority": jira_priority.strip().title(),
        "linked_incident": linked_incident,
        "comments": [],
    }

    issues.append(new_issue)
    save_jira_issues(issues)

    return {
        "status": "created",
        "issue": new_issue,
    }
@mcp.tool()
def add_jira_comment(
    issue_key: str,
    comment: str,
    incident_priority: str,
    approved: bool = False,
) -> dict:
    """Add a comment to a fictional Jira issue."""
    issue_key = issue_key.strip().upper()
    comment = comment.strip()
    incident_priority = incident_priority.strip().upper()

    if not comment:
        return {
            "status": "blocked",
            "reason": "Comment cannot be empty.",
        }

    if incident_priority in {"P1", "P2"} and not approved:
        return {
            "status": "approval_required",
            "reason": (
                f"{incident_priority} incident updates require "
                "human approval."
            ),
        }

    issues = load_jira_issues()

    for issue in issues:
        if issue["key"] != issue_key:
            continue

        issue["comments"].append(comment)
        save_jira_issues(issues)

        return {
            "status": "updated",
            "issue_key": issue_key,
            "comment": comment,
        }

    return {
        "status": "not_found",
        "reason": f"Jira issue {issue_key} was not found.",
    }
if __name__ == "__main__":
    mcp.run()
