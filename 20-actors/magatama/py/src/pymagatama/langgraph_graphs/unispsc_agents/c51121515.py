from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    has_coa: bool
    compliant: bool

def validate_chemistry(state: ProcurementState):
    state['compliant'] = state['purity'] >= 99.0 and state['has_coa']
    return state

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_chemistry)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
