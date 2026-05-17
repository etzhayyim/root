from typing import TypedDict
from langgraph.graph import StateGraph, END

class TinExtrusionState(TypedDict):
    purity: float
    tolerance: float
    approved: bool

def validate_specs(state: TinExtrusionState):
    state['approved'] = state['purity'] >= 99.9 and state['tolerance'] <= 0.05
    return state

graph = StateGraph(TinExtrusionState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()