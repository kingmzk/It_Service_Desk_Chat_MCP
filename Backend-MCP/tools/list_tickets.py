from mcp_instance import mcp
from data.tickets_store import list_tickets as _list_tickets

@mcp.tool()
def list_tickets(status: str = "", user_email: str = "") -> list:
    """
    List all support tickets, optionally filtered.

    Args:
        status:     Filter by ticket status: open, in_progress, resolved, closed.
                    Leave empty to return tickets of all statuses.
        user_email: Filter by the email of the user who raised the ticket.
                    Leave empty to return tickets from all users.

    Returns:
        List of matching tickets sorted by creation date (newest first).
    """
    tickets = _list_tickets(
        status=status or None,
        user_email=user_email or None,
    )
    tickets_sorted = sorted(tickets, key=lambda t: t["created_at"], reverse=True)
    if not tickets_sorted:
        return [{"message": "No tickets found matching the given filters."}]
    return tickets_sorted