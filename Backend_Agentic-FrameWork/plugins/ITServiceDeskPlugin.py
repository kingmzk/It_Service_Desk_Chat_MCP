import json
import uuid
from datetime import datetime
from pathlib import Path
from semantic_kernel.functions.kernel_function_decorator import kernel_function

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"
TICKETS_FILE = DATA_DIR / "tickets" / "tickets.json"

# Ensure folders exist
KB_DIR.mkdir(parents=True, exist_ok=True)
TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)

if not TICKETS_FILE.exists():
    TICKETS_FILE.write_text("{}")

VALID_STATUSES = ["open", "in_progress", "resolved", "closed"]
VALID_PRIORITIES = ["low", "medium", "high"]

class ITServiceDeskPlugin:
    @kernel_function(
        description="Search the local knowledge base for IT articles.",
        name="search_knowledge_base"
    )
    def search_knowledge_base(self, query: str) -> str:
        results = []
        keywords = [word.lower() for word in query.split() if len(word) > 2]
        if not keywords:
            keywords = [query.lower()]
        
        for file_path in KB_DIR.glob("*.*"):
            if file_path.suffix in [".txt", ".md"]:
                content = file_path.read_text(encoding="utf-8")
                if any(kw in file_path.name.lower() or kw in content.lower() for kw in keywords):
                    results.append(f"--- Article: {file_path.name} ---\n{content}\n")
                    
        if results:
            return "\n".join(results)
        
        return f"No knowledge base articles found matching '{query}' in the data folder. Escalate to ticket."

    @kernel_function(
        description="Reads the data/tickets/tickets.json file and returns all currently open IT tickets.",
        name="get_all_open_tickets"
    )
    def get_all_open_tickets(self) -> str:
        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            open_tickets = [t for t in tickets.values() if t.get("status") in ["open", "in_progress"]]
            
            if not open_tickets:
                return "There are currently no open tickets in the system."
            
            output = "Open Tickets:\n"
            for t in open_tickets:
                output += f"- ID: {t.get('ticket_id')} | Title: {t.get('title')} | Status: {t.get('status')} | Priority: {t.get('priority')}\n"
            return output
        except Exception as e:
            return f"Error reading tickets database: {str(e)}"

    @kernel_function(
        description="Creates a new IT ticket and saves it directly to the data/tickets/tickets.json dictionary.",
        name="create_it_ticket"
    )
    def create_it_ticket(
        self,
        title: str, 
        description: str, 
        user_email: str, 
        priority: str = "medium", 
        status: str = "open", 
        category: str = "general"
    ) -> str:
        ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        
        new_ticket = {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "user_email": user_email,
            "priority": priority.lower() if priority.lower() in VALID_PRIORITIES else "medium",
            "category": category.lower(),
            "status": status.lower() if status.lower() in VALID_STATUSES else "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "notes": []
        }
        
        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            tickets[ticket_id] = new_ticket
            TICKETS_FILE.write_text(json.dumps(tickets, indent=4))
            
            return f"Ticket successfully created and saved to disk! Ticket ID: {ticket_id}"
        except Exception as e:
            return f"Failed to save ticket to disk: {str(e)}"
        
    @kernel_function(
        description="Fetch the details and current status of a specific IT ticket by its ID.",
        name="get_ticket_status"
    )
    def get_ticket_status(self, ticket_id: str) -> str:
        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            t = tickets.get(ticket_id.upper())
            
            if t:
                return f"Ticket {ticket_id} Found:\nTitle: {t.get('title')}\nStatus: {t.get('status')}\nEmail: {t.get('user_email')}\nPriority: {t.get('priority')}"
                    
            return f"Error: Ticket '{ticket_id}' not found in the database."
        except Exception as e:
            return f"Error reading tickets database: {str(e)}"

    @kernel_function(
        description="Update the status of an existing IT ticket. Valid statuses are: 'open', 'in_progress', 'resolved', 'closed'.",
        name="update_ticket_status"
    )
    def update_ticket_status(self, ticket_id: str, new_status: str) -> str:
        target_status = new_status.lower()
        if target_status not in VALID_STATUSES:
            return f"Error: Invalid status '{new_status}'. Must be one of {VALID_STATUSES}."

        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            tid = ticket_id.upper()
            
            if tid not in tickets:
                return f"Error: Ticket '{ticket_id}' not found."

            tickets[tid]["status"] = target_status
            tickets[tid]["updated_at"] = datetime.utcnow().isoformat()
            
            TICKETS_FILE.write_text(json.dumps(tickets, indent=4))
            return f"Success! Ticket {ticket_id} has been updated to '{target_status}'."
        except Exception as e:
            return f"Failed to update ticket status: {str(e)}"

    @kernel_function(
        description="Escalate a ticket to high priority when a user is blocked or reporting an urgent issue.",
        name="escalate_ticket"
    )
    def escalate_ticket(self, ticket_id: str, reason: str) -> str:
        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            tid = ticket_id.upper()
            
            if tid not in tickets:
                return f"Error: Ticket '{ticket_id}' not found."

            tickets[tid]["status"] = "in_progress"
            tickets[tid]["priority"] = "high"
            tickets[tid]["updated_at"] = datetime.utcnow().isoformat()
            
            if "notes" not in tickets[tid]:
                tickets[tid]["notes"] = []
            tickets[tid]["notes"].append(f"ESCALATED: {reason}")
            
            TICKETS_FILE.write_text(json.dumps(tickets, indent=4))
            return f"Success! Ticket {ticket_id} has been escalated to High Priority. Reason logged: {reason}"
        except Exception as e:
            return f"Failed to escalate ticket: {str(e)}"
