from typing import TypedDict
from langgraph.graph import StateGraph, END

class GratingState(TypedDict):
    specs: dict
    validated: bool

def validate_load_specs(state: GratingState):
    capacity = state['specs'].get('load_capacity', 0)
    return {'validated': capacity > 500}

def process_procurement(state: GratingState):
    return state

graph = StateGraph(GratingState)
graph.add_node('validate', validate_load_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
