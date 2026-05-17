from typing import TypedDict
from langgraph.graph import StateGraph, END

class LampState(TypedDict):
    voltage: float
    base_type: str
    is_compliant: bool

def validate_lamp_spec(state: LampState):
    state['is_compliant'] = state['voltage'] > 0 and state['base_type'] != ''
    return state

def approval_node(state: LampState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(LampState)
graph.add_node('validate', validate_lamp_spec)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()