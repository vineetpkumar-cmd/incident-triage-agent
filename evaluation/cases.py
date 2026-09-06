import json
from pathlib import Path


CASE_FILE = Path(__file__).with_name("golden_cases.json")

SCENARIOS = {
    "happy_path",
    "edge_case",
    "known_failure",
    "adversarial",
}

DECISIONS = {
    "wait",
    "notify",
    "escalate",
}

JIRA_ACTIONS = {
    "none",
    "create",
    "update",
}

EMAIL_ACTIONS = {
    "none",
    "draft",
    "send",
}


def validate_case(case: dict) -> None:
    """Validate one golden evaluation case."""
    required = {
        "case_id",
        "scenario_type",
        "difficulty",
        "incident",
        "jira_issues",
        "approval_response",
        "expected",
        "rationale",
    }

    missing = required - case.keys()

    if missing:
        raise ValueError(
            f"Missing case fields: {sorted(missing)}"
        )

    if case["scenario_type"] not in SCENARIOS:
        raise ValueError("Unknown scenario_type")

    expected = case["expected"]

    if expected["decision"] not in DECISIONS:
        raise ValueError("Unknown decision")

    if expected["jira_action"] not in JIRA_ACTIONS:
        raise ValueError("Unknown jira_action")

    if expected["email_action"] not in EMAIL_ACTIONS:
        raise ValueError("Unknown email_action")

    if (
        case["incident"].get("priority") in {"P1", "P2"}
        and not expected["approval_required"]
    ):
        raise ValueError("P1/P2 cases require approval")


def load_cases(
    path: Path | None = None,
) -> list[dict]:
    """Load and validate the golden evaluation cases."""
    case_path = path or CASE_FILE

    cases = json.loads(
        case_path.read_text(encoding="utf-8")
    )

    for case in cases:
        validate_case(case)

    return cases