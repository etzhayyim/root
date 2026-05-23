from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_name: str
    gmp_status: bool
    purity: float
    approved: bool

def validate_api(state: ProcurementState):
    state['approved'] = state['gmp_status'] and state['purity'] >= 0.99
    return state

def route_procurement(state: ProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_api)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
