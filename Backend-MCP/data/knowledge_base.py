# ── Static knowledge base ─────────────────────────────────────
# Searchable articles for common IT issues
ARTICLES: list[dict] = [
    {
        "id": "KB001",
        "title": "Reset Windows Password",
        "category": "account",
        "keywords": ["password", "reset", "login", "locked out", "windows"],
        "solution": (
            "1. Press Ctrl+Alt+Del → 'Change a password'.\n"
            "2. If locked out, contact IT at it-support@company.com.\n"
            "3. For self-service reset, visit https://aka.ms/sspr with your work email."
        ),
    },
    {
        "id": "KB002",
        "title": "VPN Connection Issues",
        "category": "network",
        "keywords": ["vpn", "network", "connect", "remote", "cisco", "anyconnect"],
        "solution": (
            "1. Ensure Cisco AnyConnect is installed and updated.\n"
            "2. Connect to vpn.company.com with your AD credentials.\n"
            "3. If MFA prompt doesn't appear, restart the AnyConnect service.\n"
            "4. Still failing? Run: 'sc restart vpnagent' as admin."
        ),
    },
    {
        "id": "KB003",
        "title": "Outlook Not Syncing Email",
        "category": "email",
        "keywords": ["outlook", "email", "sync", "not receiving", "stuck", "calendar"],
        "solution": (
            "1. Check internet connection and VPN status.\n"
            "2. In Outlook: File → Account Settings → Repair your account.\n"
            "3. Clear cache: close Outlook, delete %localappdata%\\Microsoft\\Outlook\\*.ost.\n"
            "4. Restart Outlook — initial sync may take 10–15 minutes."
        ),
    },
    {
        "id": "KB004",
        "title": "Laptop Running Slow",
        "category": "hardware",
        "keywords": ["slow", "performance", "lag", "freeze", "hang", "memory", "cpu"],
        "solution": (
            "1. Restart the laptop — clears memory leaks.\n"
            "2. Open Task Manager (Ctrl+Shift+Esc) → identify high CPU/RAM processes.\n"
            "3. Run Windows Update and restart.\n"
            "4. If SSD usage is >90%, free up space or raise a storage ticket."
        ),
    },
    {
        "id": "KB005",
        "title": "Software Installation Request",
        "category": "software",
        "keywords": ["install", "software", "application", "license", "request"],
        "solution": (
            "1. Check the approved software list on the intranet portal.\n"
            "2. Approved software: submit request via IT portal → 'Software Request'.\n"
            "3. Non-listed software requires manager + IT security approval (2–3 days).\n"
            "4. Emergency installs: raise a critical priority ticket."
        ),
    },
]

def search_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
    """
    Simple keyword-match search over KB articles.
    Returns up to top_k articles ranked by keyword hit count.
    """
    query_words = set(query.lower().split())
    scored = []
    for article in ARTICLES:
        hits = sum(1 for kw in article["keywords"] if kw in query_words or kw in query.lower())
        if hits > 0:
            scored.append((hits, article))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [article for _, article in scored[:top_k]]