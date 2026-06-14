from mcp_instance import mcp
from data.knowledge_base import search_knowledge_base as _search_kb

@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 3) -> list:
    """
    Search the IT knowledge base for solutions to common issues.
    Always call this BEFORE creating a ticket — the user may be able to
    self-serve from an existing article.

    Args:
        query: Natural language description of the problem (e.g. "can't connect to VPN").
        top_k: Maximum number of articles to return (default 3).

    Returns:
        List of matching KB articles with title, category, and solution steps.
        Returns an empty list if no relevant articles are found.
    """
    results = _search_kb(query=query, top_k=top_k)
    if not results:
        return [{"message": "No matching articles found. Consider creating a support ticket."}]
    return results