from mcp_instance import mcp
from data.tickets_store import get_ticket as _get_ticket

@mcp.tool()
def get_ticket_status(ticket_id: str) -> dict:
    """
    Retrieve the current status and details of a support ticket.

    Args:
        ticket_id: The ticket ID (e.g. TKT-A1B2C3D4).

    Returns:
        Full ticket details including status, priority, notes, and timestamps.
        Returns an error dict if the ticket is not found.
    """
    ticket = _get_ticket(ticket_id)
    if ticket is None:
        return {"error": f"Ticket '{ticket_id}' not found."}
    return ticket