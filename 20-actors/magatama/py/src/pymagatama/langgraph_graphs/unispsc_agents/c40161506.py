from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterSpec(TypedDict):
    capacity: float
    material: str
    is_validated: bool

def validate_specs(state: FilterSpec):
    state['is_validated'] = state['capacity'] > 0 and len(state['material']) > 0
    return state

graph = StateGraph(FilterSpec)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()