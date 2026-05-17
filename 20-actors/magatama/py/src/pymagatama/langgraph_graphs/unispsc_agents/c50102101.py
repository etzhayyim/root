from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ApricotProcurementState(TypedDict):
    origin: str
    quality_score: float
    phytosanitary_certs: List[str]
    is_approved: bool

def validate_freshness(state: ApricotProcurementState):
    # Simulate quality inspection logic for perishables
    state['is_approved'] = state['quality_score'] >= 0.8 and len(state['phytosanitary_certs']) > 0
    return state

def route_procurement(state: ApricotProcurementState):
    return 'approve' if state['is_approved'] else 'reject'

graph = StateGraph(ApricotProcurementState)
graph.add_node('inspector', validate_freshness)
graph.set_entry_point('inspector')
graph.add_edge('inspector', END)
graph.compile()