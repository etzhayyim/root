from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrushState(TypedDict):
    material: str
    rpm_limit: int
    validated: bool

def validate_spec(state: BrushState):
    state['validated'] = state['rpm_limit'] > 0 and state['material'] in ['Steel', 'Brass', 'Stainless']
    return state

graph = StateGraph(BrushState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()