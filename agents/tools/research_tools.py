"""Web search tool for Researcher agent — uses Anthropic native web_search."""


def tool_definitions() -> list[dict]:
    """Anthropic web_search tool — server-side, не нужно реализовывать executor."""
    return [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5,
        }
    ]
