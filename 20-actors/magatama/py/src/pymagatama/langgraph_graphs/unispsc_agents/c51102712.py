from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntisepticState(TypedDict):
    purity: float
    compliant: bool
    safety_verified: bool

def validate_purity(state: AntisepticState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def verify_safety(state: AntisepticState):
    state['safety_verified'] = True
    return state

graph = StateGraph(AntisepticState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', verify_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
