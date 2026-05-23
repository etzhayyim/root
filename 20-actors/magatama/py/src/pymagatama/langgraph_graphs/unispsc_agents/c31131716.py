from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    purity: float
    weight: float
    verified: bool

def validate_precious_metal(state: ForgingState):
    is_valid = state['purity'] >= 0.999 and state['weight'] > 0
    return {'verified': is_valid}

def security_protocol(state: ForgingState):
    return {'verified': state['verified'] and True}

graph = StateGraph(ForgingState)
graph.add_node('validation', validate_precious_metal)
graph.add_node('security', security_protocol)
graph.set_entry_point('validation')
graph.add_edge('validation', 'security')
graph.add_edge('security', END)
graph = graph.compile()
