from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HalothaneState(TypedDict):
    purity: float
    gmp_valid: bool
    clearance_status: str

def validate_quality(state: HalothaneState):
    if state['purity'] < 0.999:
        return {'clearance_status': 'REJECTED'}
    return {'clearance_status': 'QA_PASSED'}

def check_compliance(state: HalothaneState):
    if not state.get('gmp_valid'):
        return {'clearance_status': 'COMPLIANCE_FAILURE'}
    return {'clearance_status': 'READY_FOR_SHIPMENT'}

graph = StateGraph(HalothaneState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()