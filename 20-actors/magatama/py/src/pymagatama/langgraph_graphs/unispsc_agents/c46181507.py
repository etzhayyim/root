from langgraph.graph import StateGraph, END
from typing import TypedDict

class SafetyVestState(TypedDict):
    visibility_class: str
    compliance_cert: bool
    is_approved: bool

def validate_ansi_compliance(state: SafetyVestState):
    state['is_approved'] = state['visibility_class'] in ['Class 1', 'Class 2', 'Class 3'] and state['compliance_cert']
    return state

graph = StateGraph(SafetyVestState)
graph.add_node('validate', validate_ansi_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()