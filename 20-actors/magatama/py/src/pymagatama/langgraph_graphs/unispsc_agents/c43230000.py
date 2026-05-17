from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    license_key: str
    compatibility_check: bool
    security_approved: bool

def validate_license(state: SoftwareState):
    state['compatibility_check'] = len(state['license_key']) > 10
    return state

def approval_step(state: SoftwareState):
    state['security_approved'] = True
    return state

graph = StateGraph(SoftwareState)
graph.add_node('validate', validate_license)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()