from evaluation.upload_dataset import (
    to_langsmith_example,
)


def test_case_is_split_for_langsmith():
    case = {
        "case_id": "HP-001",
        "scenario_type": "happy_path",
        "difficulty": "easy",
        "incident": {
            "number": "INC1000001",
            "priority": "P1",
        },
        "jira_issues": [],
        "approval_response": {
            "approved": True,
            "feedback": "",
        },
        "expected": {
            "decision": "escalate",
        },
        "rationale": "P1 escalates.",
    }

    example = to_langsmith_example(case)

    assert example["inputs"]["case_id"] == "HP-001"
    assert example["outputs"] == {
        "decision": "escalate",
    }
    assert (
        example["metadata"]["dataset_version"]
        == "v1"
    )