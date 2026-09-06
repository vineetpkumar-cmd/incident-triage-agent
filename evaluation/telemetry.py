from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


_ACTIVE: ContextVar[list[str] | None] = ContextVar(
    "evaluation_tool_calls",
    default=None,
)


def record_tool_call(tool_name: str) -> None:
    """Record a tool call when evaluation capture is active."""
    calls = _ACTIVE.get()

    if calls is not None:
        calls.append(tool_name)


@contextmanager
def capture_tool_calls() -> Iterator[list[str]]:
    """Capture ordered tool calls for one evaluation case."""
    calls: list[str] = []
    token = _ACTIVE.set(calls)

    try:
        yield calls
    finally:
        _ACTIVE.reset(token)