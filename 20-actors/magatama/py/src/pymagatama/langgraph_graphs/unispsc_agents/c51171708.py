from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    regulatory_id: str
    is_verified: bool

def validate_compliance(state: ProcurementState):
    state['is_verified'] = len(state['regulatory_id']) > 8 and state['purity'] >= 99.0
    return state

def shipment_approval(state: ProcurementState):
    if state['is_verified']:
        print('Regulatory checks passed for Diphenoxylate.')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('approve', shipment_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()