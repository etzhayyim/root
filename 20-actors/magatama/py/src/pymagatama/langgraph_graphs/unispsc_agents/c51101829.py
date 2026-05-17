from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    has_coa: bool
    compliant: bool

def validate_quality(state: ProcurementState) -> dict:
    is_pure = state['purity'] >= 99.0
    return {'compliant': is_pure and state['has_coa']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()