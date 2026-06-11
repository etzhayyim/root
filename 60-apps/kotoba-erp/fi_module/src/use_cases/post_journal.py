from typing import TypedDict, Annotated, List
import datetime
from src.domain.entities import BKPF, BSEG

class PostJournalState(TypedDict):
    entry_data: dict
    bkpf: BKPF | None
    validation_errors: List[str]
    status: str

def parse_entry(state: PostJournalState) -> dict:
    """Parse incoming dict to BKPF/BSEG entities."""
    data = state["entry_data"]
    items = []
    belnr = data.get("entry_id", "TEMP")
    
    for idx, l_data in enumerate(data.get("lines", [])):
        items.append(BSEG(
            belnr=belnr,
            buzei=str(idx + 1),
            hkont=l_data["account_id"],
            shkzg='S' if l_data.get("is_debit", True) else 'H',
            wrbtr=float(l_data["amount"]),
            sgtxt=l_data.get("description", "")
        ))
    
    bkpf = BKPF(
        belnr=belnr,
        bukrs="1000", # default company code
        bldat=datetime.datetime.now(),
        budat=datetime.datetime.now(),
        items=items,
        bstat="V"
    )
    return {"bkpf": bkpf}

def validate_entry(state: PostJournalState) -> dict:
    """Validate the accounting document balances."""
    bkpf: BKPF = state["bkpf"]
    errors = state.get("validation_errors", [])
    
    if not bkpf.validate_balance():
        errors.append("Accounting Document (BKPF) does not balance.")
        
    return {"validation_errors": errors}

def check_validation(state: PostJournalState) -> str:
    if len(state.get("validation_errors", [])) > 0:
        return "reject"
    return "post"

def post_entry(state: PostJournalState) -> dict:
    """Mark as POSTED and persist to Kotoba KQE via Repository Adapter."""
    bkpf: BKPF = state["bkpf"]
    bkpf.bstat = "" # Cleared V means posted
    
    from src.adapters.repository import FIRepository
    repo = FIRepository()
    repo.save_accounting_document(bkpf)
    
    return {"bkpf": bkpf, "status": "POSTED"}

def reject_entry(state: PostJournalState) -> dict:
    """Mark as REJECTED."""
    bkpf: BKPF = state["bkpf"]
    bkpf.bstat = "R" # Custom for rejected
    return {"bkpf": bkpf, "status": "REJECTED"}
