from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity: float
    gmp_status: bool
    is_compliant: bool

def validate_quality(state: ProcurementState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['gmp_status']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
