import uuid
from datetime import datetime
from typing import Optional

# ── In-memory ticket store ────────────────────────────────────
# Stores all tickets as a dict keyed by ticket_id
tickets: dict[str, dict] = {}

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_STATUSES   = {"open", "in_progress", "resolved", "closed"}

def create_ticket(
    title: str,
    description: str,
    user_email: str,
    priority: str = "medium",
    category: str = "general",
) -> dict:
    """Create a new ticket and return it."""
    ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
    ticket = {
        "ticket_id":   ticket_id,
        "title":       title,
        "description": description,
        "user_email":  user_email,
        "priority":    priority if priority in VALID_PRIORITIES else "medium",
        "category":    category,
        "status":      "open",
        "created_at":  datetime.utcnow().isoformat(),
        "updated_at":  datetime.utcnow().isoformat(),
        "notes":       [],
    }
    tickets[ticket_id] = ticket
    return ticket

def get_ticket(ticket_id: str) -> Optional[dict]:
    """Return a ticket by ID, or None if not found."""
    return tickets.get(ticket_id)

def update_ticket_status(ticket_id: str, status: str, note: str = "") -> Optional[dict]:
    """Update a ticket's status. Optionally append a note."""
    ticket = tickets.get(ticket_id)
    if not ticket:
        return None
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")
    ticket["status"]     = status
    ticket["updated_at"] = datetime.utcnow().isoformat()
    if note:
        ticket["notes"].append({"text": note, "timestamp": datetime.utcnow().isoformat()})
    return ticket

def list_tickets(status: Optional[str] = None, user_email: Optional[str] = None) -> list[dict]:
    """Return all tickets, optionally filtered by status and/or user_email."""
    result = list(tickets.values())
    if status:
        result = [t for t in result if t["status"] == status]
    if user_email:
        result = [t for t in result if t["user_email"] == user_email]
    return result

def escalate_ticket(ticket_id: str, reason: str) -> Optional[dict]:
    """Escalate a ticket to high priority and mark it in_progress."""
    ticket = tickets.get(ticket_id)
    if not ticket:
        return None
    ticket["priority"]   = "high"
    ticket["status"]     = "in_progress"
    ticket["updated_at"] = datetime.utcnow().isoformat()
    ticket["notes"].append({
        "text":      f"ESCALATED: {reason}",
        "timestamp": datetime.utcnow().isoformat(),
    })
    return ticket