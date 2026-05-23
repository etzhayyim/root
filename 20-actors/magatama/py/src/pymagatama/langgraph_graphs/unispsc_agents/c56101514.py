from typing import TypedDict
from langgraph.graph import StateGraph, END

class FootStoolState(TypedDict):
    spec_data: dict
    validated: bool

def validate_load(state: FootStoolState):
    capacity = state['spec_data'].get('load_capacity_kg', 0)
    return {'validated': capacity >= 100}

graph = StateGraph(FootStoolState)
graph.add_node('validate', validate_load)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
