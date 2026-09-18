import pytest

from red_team.compare import compare_runs


def evidence(case_id, verdict, family="prompt_injection"):
    return {
        "case_id": case_id,
        "attack_family": family,
        "verdict": verdict,
        "reasons": [],
    }


def test_comparison_rejects_mismatched_case_ids():
    with pytest.raises(ValueError, match="case IDs differ"):
        compare_runs([evidence("A", "PASS")], [evidence("B", "PASS")])


def test_comparison_reports_transitions_and_control_utility():
    baseline = [
        evidence("ATTACK", "FAIL", "prompt_injection"),
        evidence("CTRL", "PASS", "legitimate_control"),
    ]
    defended = [
        evidence("ATTACK", "PASS", "prompt_injection"),
        evidence("CTRL", "WARN", "legitimate_control"),
    ]
    result = compare_runs(baseline, defended)
    assert result["transitions"] == {"FAIL->PASS": 1, "PASS->WARN": 1}
    assert result["baseline"]["safety_pass_rate"] == 0.0
    assert result["defended"]["safety_pass_rate"] == 1.0
    assert result["defended"]["control_completion_rate"] == 0.0
    assert result["remaining_failures"] == []
    assert result["utility_regressions"] == ["CTRL"]


def test_comparison_rejects_duplicate_case_ids():
    duplicate = [evidence("A", "PASS"), evidence("A", "FAIL")]
    with pytest.raises(ValueError, match="duplicate case IDs"):
        compare_runs(duplicate, duplicate)
