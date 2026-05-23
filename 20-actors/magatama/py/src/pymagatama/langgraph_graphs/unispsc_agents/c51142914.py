from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    has_gmp_cert: bool
    is_approved: bool

def validate_pharmaceutical(state: ProcurementState) -> dict:
    if state['purity_level'] >= 99.0 and state['has_gmp_cert']:
        return {'is_approved': True}
    return {'is_approved': False}

def route_by_approval(state: ProcurementState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharmaceutical)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
app = graph.compile()
