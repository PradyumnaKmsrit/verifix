"""A tiny pub-sub hook so agents can report progress to whoever is listening
(the CLI's print statements, or the API's SSE stream), without agents.py
needing to know which one is in use."""

from contextvars import ContextVar
from typing import Callable

Listener = Callable[[str, str], None]

_listener: ContextVar[Listener | None] = ContextVar("verifix_listener", default=None)


def emit(node: str, message: str) -> None:
    """Report progress from an agent node. Always prints; also forwards to
    whichever listener is active for this run, if any."""
    print(f"[{node}] {message}")
    listener = _listener.get()
    if listener is not None:
        listener(node, message)


def set_listener(listener: Listener | None):
    """Register a listener for the current context. Returns a token to reset with."""
    return _listener.set(listener)


def reset_listener(token) -> None:
    _listener.set(token.old_value if hasattr(token, "old_value") else None)