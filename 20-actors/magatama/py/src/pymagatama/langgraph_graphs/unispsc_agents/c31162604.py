from typing import TypedDict
from langgraph.graph import StateGraph, END

class HookComplianceState(TypedDict):
    load_capacity: float
    has_safety_latch: bool
    certification: str
    is_compliant: bool

def validate_safety_hook(state: HookComplianceState):
    state['is_compliant'] = state['has_safety_latch'] and state['load_capacity'] > 0
    return state

builder = StateGraph(HookComplianceState)
builder.add_node('validation', validate_safety_hook)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()