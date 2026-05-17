from typing import TypedDict
from langgraph.graph import StateGraph, END

class PuzzleState(TypedDict):
    material_safety: bool
    safety_certification: bool
    compliant: bool

def check_compliance(state: PuzzleState):
    state['compliant'] = state['material_safety'] and state['safety_certification']
    return state

builder = StateGraph(PuzzleState)
builder.add_node('compliance_check', check_compliance)
builder.set_entry_point('compliance_check')
builder.add_edge('compliance_check', END)
graph = builder.compile()