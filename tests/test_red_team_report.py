from red_team.report import render_report


def row(case_id, family, verdict, response="Observed response", reasons=None):
    return {
        "case_id": case_id,
        "attack_family": family,
        "turns": ["Prompt tried"],
        "response": response,
        "tool_sequence": [],
        "mutations": {},
        "verdict": verdict,
        "reasons": reasons or [],
    }


def test_report_contains_required_evidence_and_defense_columns():
    baseline = [row("FAIL-CASE", "prompt_injection", "FAIL")]
    defended = [row("FAIL-CASE", "prompt_injection", "PASS")]
    comparison = {
        "case_count": 1,
        "baseline": {"pass": 0, "warn": 0, "fail": 1, "safety_pass_rate": 0.0, "control_completion_rate": 0.0},
        "defended": {"pass": 1, "warn": 0, "fail": 0, "safety_pass_rate": 1.0, "control_completion_rate": 0.0},
        "transitions": {"FAIL->PASS": 1},
        "remaining_failures": [],
        "utility_regressions": [],
    }
    report = render_report(baseline, defended, comparison)
    for heading in (
        "# Week 6 Incident Triage Red-Team Findings",
        "## Executive summary",
        "## Baseline vs defended results",
        "## Attack evidence",
        "## Legitimate-use controls",
        "## Attack-to-defense mapping",
        "## Remaining failures and next experiments",
    ):
        assert heading in report
    assert "| Case | Family | Prompt | Observed result | Verdict | Recommended defense |" in report


def test_report_keeps_failures_and_utility_regressions_visible():
    baseline = [
        row("FAIL-CASE", "prompt_injection", "FAIL"),
        row("CTRL-REGRESSION", "legitimate_control", "PASS"),
    ]
    defended = [
        row("FAIL-CASE", "prompt_injection", "FAIL"),
        row("CTRL-REGRESSION", "legitimate_control", "WARN"),
    ]
    comparison = {
        "case_count": 2,
        "baseline": {"pass": 1, "warn": 0, "fail": 1, "safety_pass_rate": 0.0, "control_completion_rate": 1.0},
        "defended": {"pass": 0, "warn": 1, "fail": 1, "safety_pass_rate": 0.0, "control_completion_rate": 0.0},
        "transitions": {"PASS->WARN": 1},
        "remaining_failures": ["FAIL-CASE"],
        "utility_regressions": ["CTRL-REGRESSION"],
    }
    report = render_report(baseline, defended, comparison)
    assert "FAIL-CASE" in report
    assert "CTRL-REGRESSION" in report
