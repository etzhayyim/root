from typing import TypedDict
from langgraph.graph import StateGraph, END

class FerrousState(TypedDict):
    purity: float
    status: str

def validate_purity(state: FerrousState):
    is_valid = state['purity'] >= 99.0
    return {'status': 'approved' if is_valid else 'rejected'}

graph = StateGraph(FerrousState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()