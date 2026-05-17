from typing import TypedDict
from langgraph.graph import StateGraph, END

class Specs(TypedDict):
    material: str
    compliance: bool

def validate_specs(state: Specs):
    if state['material'] == 'surgical-grade-steel':
        return {'compliance': True}
    return {'compliance': False}

graph = StateGraph(Specs)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()