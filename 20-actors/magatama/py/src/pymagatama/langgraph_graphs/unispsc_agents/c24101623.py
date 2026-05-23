from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraneState(TypedDict):
    capacity: float
    safety_certs: list
    validation_status: bool

def validate_crane_spec(state: CraneState):
    state['validation_status'] = state['capacity'] > 0 and len(state['safety_certs']) > 0
    return state

def check_compliance(state: CraneState):
    return 'approved' if state['validation_status'] else 'rejected'

workflow = StateGraph(CraneState)
workflow.add_node('validate', validate_crane_spec)
workflow.add_node('audit', check_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'audit')
workflow.add_edge('audit', END)
graph = workflow.compile()
