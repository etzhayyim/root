from typing import TypedDict, Annotated, List, Dict, Any
from src.domain.entities import JournalEntry, JournalEntryLine
import datetime

# We will use KotobaLangGraph if possible, but for clean architecture 
# this use case is defined independently of kotoba_langgraph details 
# as much as possible, or using it as a thin wrapper.

class PostJournalState(TypedDict):
    entry_data: dict
    journal_entry: JournalEntry | None
    validation_errors: List[str]
    status: str

def parse_entry(state: PostJournalState) -> dict:
    """Parse incoming dict to domain entity."""
    data = state["entry_data"]
    lines = []
    for l_data in data.get("lines", []):
        lines.append(JournalEntryLine(
            account_id=l_data["account_id"],
            amount=float(l_data["amount"]),
            is_debit=bool(l_data["is_debit"]),
            description=l_data.get("description", "")
        ))
    
    # We create the entry
    entry = JournalEntry(
        entry_id=data.get("entry_id", "TEMP"),
        date=datetime.datetime.now(),
        lines=lines,
        status="DRAFT"
    )
    return {"journal_entry": entry}

def validate_entry(state: PostJournalState) -> dict:
    """Validate the journal entry balances."""
    entry: JournalEntry = state["journal_entry"]
    errors = state.get("validation_errors", [])
    
    if not entry.validate_balance():
        errors.append("Journal Entry does not balance.")
        
    return {"validation_errors": errors}

def check_validation(state: PostJournalState) -> str:
    """Router logic for LangGraph."""
    if len(state.get("validation_errors", [])) > 0:
        return "reject"
    return "post"

def post_entry(state: PostJournalState) -> dict:
    """Mark as POSTED and persist to Kotoba KQE via Repository Adapter."""
    entry: JournalEntry = state["journal_entry"]
    entry.status = "POSTED"
    
    from src.adapters.repository import JournalEntryRepository
    repo = JournalEntryRepository()
    repo.save(entry)
    
    return {"journal_entry": entry, "status": "POSTED"}

def reject_entry(state: PostJournalState) -> dict:
    """Mark as REJECTED."""
    entry: JournalEntry = state["journal_entry"]
    entry.status = "REJECTED"
    return {"journal_entry": entry, "status": "REJECTED"}

# The actual graph compilation will happen in the entrypoint or adapter
