from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: GarmentState):
    required = ['material', 'size', 'safety_certified']
    compliant = all(k in state['specs'] for k in required)
    return {'is_compliant': compliant}

graph = StateGraph(GarmentState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()