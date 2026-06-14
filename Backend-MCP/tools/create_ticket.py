from mcp_instance import mcp
from data.tickets_store import create_ticket as _create_ticket

@mcp.tool()
def create_ticket(
    title: str,
    description: str,
    user_email: str,
    priority: str = "medium",
    category: str = "general",
) -> dict:
    """
    Create a new IT support ticket.

    Args:
        title:       Short summary of the issue.
        description: Full details of the problem.
        user_email:  Email address of the user raising the ticket.
        priority:    One of: low, medium, high, critical. Defaults to medium.
        category:    One of: general, account, network, hardware, software, email.

    Returns:
        The created ticket with its generated ticket_id.
    """
    return _create_ticket(
        title=title,
        description=description,
        user_email=user_email,
        priority=priority,
        category=category,
    )