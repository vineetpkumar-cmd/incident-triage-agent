from evaluation.evaluators import (
    decision_and_tool_accuracy,
    guardrail_compliance,
    task_completion,
    trajectory_correctness,
)


REFERENCE = {
    "decision": "escalate",
    "jira_action": "create",
    "approval_required": True,
    "email_action": "send",
    "final_stage": "complete",
    "tool_sequence": [
        "get_incident",
        "search_jira_issues",
        "send_email",
    ],
}


def test_task_completion_requires_stage_and_email():
    output = {
        **REFERENCE,
        "error": None,
    }

    result = task_completion(output, REFERENCE)

    assert result["key"] == "task_completion"
    assert result["score"] == 1.0


def test_decision_and_tool_accuracy_allows_half_credit():
    output = {
        "decision": "escalate",
        "jira_action": "update",
    }

    result = decision_and_tool_accuracy(
        output,
        REFERENCE,
    )

    assert result["score"] == 0.5


def test_guardrail_failure_scores_zero():
    output = {
        "approval_required": True,
        "safety_violations": [
            "high_severity_write_without_approval"
        ],
    }

    result = guardrail_compliance(
        output,
        REFERENCE,
    )

    assert result["score"] == 0.0


def test_wrong_tool_sequence_scores_zero():
    output = {
        "tool_sequence": [
            "search_jira_issues",
            "get_incident",
            "send_email",
        ]
    }

    result = trajectory_correctness(
        output,
        REFERENCE,
    )

    assert result["score"] == 0.0