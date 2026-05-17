from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    gmp_certified: bool
    vendor_approved: bool
    validation_status: str

def validate_purity(state: ProcurementState):
    if state['purity_level'] >= 99.0:
        return {'validation_status': 'PASSED'}
    return {'validation_status': 'FAILED'}

def check_compliance(state: ProcurementState):
    if state['gmp_certified'] and state['vendor_approved']:
        return {'validation_status': 'READY_FOR_PURCHASE'}
    return {'validation_status': 'PENDING_AUDIT'}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()