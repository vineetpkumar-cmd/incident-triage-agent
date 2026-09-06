from src.workflow import (
    prepare_retrieval_retry,
    route_after_evidence,
    route_after_retrieval,
    route_after_retrieval_review,
)


def test_sufficient_evidence_continues():
    state = {
        "evidence_status": "sufficient",
        "retry_count": 0,
    }

    assert route_after_evidence(state) == "continue"


def test_first_incomplete_result_retries():
    state = {
        "evidence_status": "insufficient",
        "retry_count": 0,
    }

    assert route_after_evidence(state) == "retry"


def test_second_incomplete_result_requests_human():
    state = {
        "evidence_status": "insufficient",
        "retry_count": 1,
    }

    assert route_after_evidence(state) == "human_review"


def test_retry_preparation_clears_old_evidence():
    state = {
        "retry_count": 0,
        "incident": {"number": "INC0010001"},
        "sla": {"sla_breached": False},
        "related_incidents": {"total": 0},
        "jira_search": {"total": 0},
        "error": "old error",
    }

    result = prepare_retrieval_retry(state)

    assert result["retry_count"] == 1
    assert result["incident"] == {}
    assert result["sla"] == {}
    assert result["related_incidents"] == {}
    assert result["jira_search"] == {}
    assert result["error"] is None
    assert result["stage"] == "retrieval_retry_prepared"


def test_failed_incident_retrieval_is_assessed():
    state = {
        "error": "Incident was not found.",
    }

    assert route_after_retrieval(state) == "assess"


def test_human_can_request_another_retry():
    state = {
        "retrieval_review_action": "retry",
    }

    assert route_after_retrieval_review(state) == "retry"


def test_human_can_stop_retrieval():
    state = {
        "retrieval_review_action": "stop",
    }

    assert route_after_retrieval_review(state) == "stop"
