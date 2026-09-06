from evaluation.ollama_judge import (
    parse_judge_response,
)


def test_valid_judge_json():
    result = parse_judge_response(
        '{"factuality":1,"clarity":0.75,'
        '"tone":1,"completeness":0.5,'
        '"reason":"Missing SLA detail."}'
    )

    assert result["score"] == 0.8125


def test_invalid_judge_json_has_no_score():
    result = parse_judge_response("not json")

    assert result["score"] is None
    assert "invalid" in result["reason"].lower()