from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrolleyState(TypedDict):
    specs: dict
    approved: bool

def validate_load_capacity(state: TrolleyState):
    capacity = state['specs'].get('load_capacity_kg', 0)
    return {'approved': capacity > 0}

graph = StateGraph(TrolleyState)
graph.add_node('validate', validate_load_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
