from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class MetalProcurementState(TypedDict):
    purity_level: float
    origin: str
    inspection_status: str
    is_compliant: bool

def validate_purity(state: MetalProcurementState):
    state['is_compliant'] = state['purity_level'] >= 99.99
    return state

def check_compliance(state: MetalProcurementState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

def mark_approved(state: MetalProcurementState):
    state['inspection_status'] = 'APPROVED'
    return state

def mark_rejected(state: MetalProcurementState):
    state['inspection_status'] = 'REJECTED'
    return state

graph = StateGraph(MetalProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('approve', mark_approved)
graph.add_node('reject', mark_rejected)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': 'approve', 'non_compliant': 'reject'})
graph.add_edge('approve', END)
graph.add_edge('reject', END)
compile = graph.compile()
