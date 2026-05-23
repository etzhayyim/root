from typing import TypedDict
from langgraph.graph import StateGraph, END

class ControllerState(TypedDict):
    model_number: str
    spec_check: bool
    compliance_verified: bool

def validate_controller(state: ControllerState):
    state['spec_check'] = 'cpu' in state['model_number'].lower()
    return state

def verify_safety(state: ControllerState):
    state['compliance_verified'] = True
    return state

graph = StateGraph(ControllerState)
graph.add_node('validate', validate_controller)
graph.add_node('safety', verify_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)

graph = graph.compile()
