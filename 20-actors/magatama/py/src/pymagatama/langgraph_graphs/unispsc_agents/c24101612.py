from typing import TypedDict
from langgraph.graph import StateGraph, END

class JackState(TypedDict):
    load_capacity: float
    safety_verified: bool
    approved: bool

def validate_capacity(state: JackState):
    if state['load_capacity'] > 0:
        return {'safety_verified': True}
    return {'safety_verified': False}

def approval_check(state: JackState):
    if state['safety_verified']:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(JackState)
graph.add_node('validate', validate_capacity)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()