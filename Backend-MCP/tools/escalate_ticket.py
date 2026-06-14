from mcp_instance import mcp
from data.tickets_store import escalate_ticket as _escalate_ticket

@mcp.tool()
def escalate_ticket(ticket_id: str, reason: str) -> dict:
    """
    Escalate an existing ticket to high priority and move it to in_progress.
    Use this when the issue is business-critical or unresolved for too long.

    Args:
        ticket_id: The ticket ID to escalate (e.g. TKT-A1B2C3D4).
        reason:    Brief explanation of why escalation is needed.

    Returns:
        Updated ticket with priority=high and status=in_progress.
        Returns an error dict if the ticket is not found.
    """
    ticket = _escalate_ticket(ticket_id=ticket_id, reason=reason)
    if ticket is None:
        return {"error": f"Ticket '{ticket_id}' not found."}
    return ticket