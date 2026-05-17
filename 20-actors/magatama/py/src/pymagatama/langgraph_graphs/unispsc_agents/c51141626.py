from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    quality_status: str
    compliance_validated: bool

def validate_quality(state: ProcurementState):
    # Simulate pharmaceutical quality validation logic
    state['quality_status'] = 'PASSED' if state['batch_id'].startswith('PRT') else 'FAILED'
    return state

def check_compliance(state: ProcurementState):
    state['compliance_validated'] = state['quality_status'] == 'PASSED'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_quality', validate_quality)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_quality')
graph.add_edge('validate_quality', 'check_compliance')
graph.add_edge('check_compliance', END)

compile_graph = graph.compile()