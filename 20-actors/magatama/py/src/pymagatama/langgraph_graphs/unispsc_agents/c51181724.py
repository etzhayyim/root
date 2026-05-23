from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    purity_level: float
    has_coa: bool
    approved: bool

def validate_quality(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0 and state['has_coa']
    return state

def route_procurement(state: ProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
