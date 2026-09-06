from src.review import (
    build_review_response,
    is_retrieval_review,
)


def test_identifies_retrieval_review():
    request = {"review_type": "retrieval"}

    assert is_retrieval_review(request) is True


def test_identifies_action_review():
    request = {"review_type": "action"}

    assert is_retrieval_review(request) is False


def test_builds_retrieval_retry_response():
    response = build_review_response(
        {"review_type": "retrieval"},
        accepted=True,
        feedback="ServiceNow is available again.",
    )

    assert response == {
        "retry": True,
        "feedback": "ServiceNow is available again.",
    }


def test_builds_action_approval_response():
    response = build_review_response(
        {"review_type": "action"},
        accepted=True,
        feedback="Approved by incident manager.",
    )

    assert response == {
        "approved": True,
        "feedback": "Approved by incident manager.",
    }