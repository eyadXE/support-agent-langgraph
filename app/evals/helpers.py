"""Shared helpers for inspecting what an agent run actually did."""


def get_called_tools(result: dict) -> set:
    """Return the set of tool names the agent invoked during this run,
    by scanning AIMessages for tool_calls. This is what lets eval cases
    assert on BEHAVIOUR (which tools ran) rather than just answer text.
    """
    called = set()
    for msg in result.get("messages", []):
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    called.add(name)
    return called


def get_reply_text(result: dict) -> str:
    """Best-effort final reply text, or '' if the run paused (interrupted)."""
    if result.get("__interrupt__"):
        return ""
    messages = result.get("messages", [])
    if not messages:
        return ""
    return messages[-1].content or ""


def was_interrupted(result: dict) -> bool:
    return bool(result.get("__interrupt__"))
