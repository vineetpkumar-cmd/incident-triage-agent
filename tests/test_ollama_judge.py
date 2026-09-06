from evaluation.ollama_judge import (
    build_judge_prompt,
    parse_judge_response,
)


def test_valid_judge_json():
    result = parse_judge_response(
        '{"factuality":1,"clarity":0.75,'
        '"tone":1,"completeness":0.5,'
        '"reason":"Missing SLA detail."}'
    )

    assert result["score"] == 0.8125
    assert set(result) == {
        "key",
        "score",
        "comment",
    }
    assert "factuality=1.0" in result["comment"]
    assert "Missing SLA detail." in result[
        "comment"
    ]


def test_invalid_judge_json_has_no_score():
    result = parse_judge_response("not json")

    assert result["score"] is None
    assert set(result) == {
        "key",
        "score",
        "comment",
    }
    assert "invalid" in result["comment"].lower()


def test_prompt_uses_evidence_as_source_of_truth():
    prompt = build_judge_prompt(
        {
            "incident": {
                "number": "INC1000001",
            },
            "decision": "escalate",
            "email_subject": "P1 incident",
            "email_body": "Incident INC1000001.",
        }
    )

    assert (
        "authoritative source of truth"
        in prompt
    )
    assert (
        "Do not penalize it for being fictional"
        in prompt
    )