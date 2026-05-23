from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec: dict
    approved: bool
    compliance_check: bool

def validate_gmp(state: ProcurementState):
    state['compliance_check'] = state['spec'].get('gmp_cert') == True
    return state

def approve_procurement(state: ProcurementState):
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gmp)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
