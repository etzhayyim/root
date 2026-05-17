from typing import TypedDict
from langgraph.graph import StateGraph, END

class UrinalysisState(TypedDict):
    lot_number: str
    expiry_date: str
    is_compliant: bool

def validate_strip_compliance(state: UrinalysisState) -> UrinalysisState:
    # Logic to verify health compliance and expiration
    state['is_compliant'] = bool(state['lot_number'] and state['expiry_date'])
    print(f'Validating lot: {state.get("lot_number")}')
    return state

builder = StateGraph(UrinalysisState)
builder.add_node("validate", validate_strip_compliance)
builder.set_entry_point("validate")
builder.add_edge("validate", END)
graph = builder.compile()