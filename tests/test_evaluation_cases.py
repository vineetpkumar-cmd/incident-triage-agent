from collections import Counter

import pytest

from evaluation.cases import load_cases, validate_case


def test_exact_dataset_size_and_mix():
    cases = load_cases()

    assert len(cases) == 40
    assert len({case["case_id"] for case in cases}) == 40
    assert Counter(case["scenario_type"] for case in cases) == {
        "happy_path": 20,
        "edge_case": 12,
        "known_failure": 6,
        "adversarial": 2,
    }


def test_every_case_has_scoreable_labels():
    required = {
        "decision",
        "jira_action",
        "approval_required",
        "email_action",
        "final_stage",
        "tool_sequence",
        "safety_expected",
    }

    for case in load_cases():
        assert required <= case["expected"].keys()


def test_p1_cannot_be_labelled_without_approval():
    case = {
        "case_id": "INVALID-001",
        "scenario_type": "edge_case",
        "difficulty": "medium",
        "incident": {"number": "INC9999999", "priority": "P1"},
        "jira_issues": [],
        "approval_response": None,
        "expected": {
            "decision": "escalate",
            "jira_action": "none",
            "approval_required": False,
            "email_action": "none",
            "final_stage": "complete",
            "tool_sequence": [],
            "safety_expected": True,
        },
        "rationale": "Contradictory test fixture.",
    }

    with pytest.raises(ValueError, match="P1/P2 cases require approval"):
        validate_case(case)
