from typing import TypedDict
from src.use_cases.post_journal import PostJournalState

class EventRouterState(TypedDict):
    ctx_payload: dict
    mapped_journal_data: dict | None
    route: str

def parse_incoming_payload(state: EventRouterState) -> dict:
    """Determine if payload is a direct Journal Entry command or an Event."""
    payload = state["ctx_payload"]
    event_type = payload.get("event_type")

    if event_type == "GoodsReceiptPosted":
        return {"route": "map_mm_receipt"}

    # Default: assume it's a direct journal entry request
    return {"route": "direct_journal", "mapped_journal_data": payload}

def map_mm_receipt(state: EventRouterState) -> dict:
    """Map a GoodsReceiptPosted event to a Journal Entry payload."""
    payload = state["ctx_payload"]
    receipt_id = payload.get("receipt_id", "UNKNOWN")
    po_number = payload.get("po_number", "UNKNOWN")
    total_value = float(payload.get("total_value", 0.0))

    journal_data = {
        "entry_id": f"JE-{receipt_id}",
        "lines": [
            {
                "account_id": "1300", # Inventory Asset Account
                "amount": total_value,
                "is_debit": True,
                "description": f"Goods Receipt {receipt_id} for PO {po_number}"
            },
            {
                "account_id": "2110", # GR/IR Clearing Account (Liability)
                "amount": total_value,
                "is_debit": False,
                "description": f"Goods Receipt {receipt_id} for PO {po_number}"
            }
        ]
    }
    return {"mapped_journal_data": journal_data}

def route_event(state: EventRouterState) -> str:
    return state["route"]
