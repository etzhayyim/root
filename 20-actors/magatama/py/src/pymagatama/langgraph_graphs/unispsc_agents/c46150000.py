from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EnforcementState(TypedDict):
    item_id: str
    compliance_check: bool
    export_control_status: str

def validate_compliance(state: EnforcementState):
    state['compliance_check'] = True
    return state

def check_dual_use(state: EnforcementState):
    state['export_control_status'] = 'CLEARED' if state['item_id'] else 'REVIEW_REQUIRED'
    return state

graph = StateGraph(EnforcementState)
graph.add_node('validate', validate_compliance)
graph.add_node('export', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
