from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_id: str
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    # Simulate CAD integration and validation
    state['approved'] = all(k in state['specs'] for k in ['material', 'tolerance'])
    print(f"Validation check for {state['part_id']}: {state['approved']}")
    return state

builder = StateGraph(ProcurementState)
builder.add_node("validate", validate_specs)
builder.set_entry_point("validate")
builder.add_edge("validate", END)
graph = builder.compile()
