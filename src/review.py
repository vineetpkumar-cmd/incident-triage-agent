def is_retrieval_review(request: dict) -> bool:
    """Return whether an interrupt concerns retrieval."""
    return request.get("review_type") == "retrieval"


def build_review_response(
    request: dict,
    accepted: bool,
    feedback: str,
) -> dict:
    """Build the correct LangGraph resume payload."""
    if is_retrieval_review(request):
        return {
            "retry": accepted,
            "feedback": feedback,
        }

    return {
        "approved": accepted,
        "feedback": feedback,
    }