import pytest

from evaluation.compare_experiments import (
    aggregate_case_scores,
    compare_case_outputs,
    human_average,
)


def test_compare_case_outputs_requires_identical_case_ids():
    baseline = [{"case_id": "A", "scores": {"task_completion": 1.0}}]
    improved = [{"case_id": "B", "scores": {"task_completion": 1.0}}]

    with pytest.raises(ValueError, match="case IDs differ"):
        compare_case_outputs(baseline, improved)


def test_aggregate_case_scores_uses_available_scores_only():
    cases = [
        {
            "case_id": "A",
            "scores": {
                "task_completion": 1.0,
                "notification_quality": 1.0,
            },
        },
        {
            "case_id": "B",
            "scores": {
                "task_completion": 0.0,
                "notification_quality": None,
            },
        },
    ]

    result = aggregate_case_scores(cases)

    assert result["task_completion"] == {"mean": 0.5, "count": 2}
    assert result["notification_quality"] == {"mean": 1.0, "count": 1}


def test_comparison_preserves_case_level_task_completion_failures():
    baseline = [
        {"case_id": "A", "scores": {"task_completion": 1.0}},
        {"case_id": "FAIL-004", "scores": {"task_completion": 0.0}},
    ]
    improved = [
        {"case_id": "A", "scores": {"task_completion": 1.0}},
        {"case_id": "FAIL-004", "scores": {"task_completion": 0.0}},
    ]

    result = compare_case_outputs(baseline, improved)

    assert result["task_completion_failures"] == {
        "baseline": ["FAIL-004"],
        "improved": ["FAIL-004"],
    }


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ([1, 1, 1, 0], 0.75),
        ([0, 1, 1, 0], 0.50),
        ([1, 1, 0, 0], 0.50),
    ],
)
def test_human_average(scores, expected):
    assert human_average(scores) == expected
