from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ThyroidProcurementState(TypedDict):
    product_sku: str
    compliance_docs: List[str]
    temp_log_verified: bool
    approved: bool

def validate_compliance(state: ThyroidProcurementState):
    state['approved'] = 'GMP_Certificate' in state['compliance_docs']
    return state

def verify_cold_chain(state: ThyroidProcurementState):
    if state['approved']:
        state['temp_log_verified'] = True
    return state

graph = StateGraph(ThyroidProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('cold_chain', verify_cold_chain)
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph.set_entry_point('validate')
graph = graph.compile()
