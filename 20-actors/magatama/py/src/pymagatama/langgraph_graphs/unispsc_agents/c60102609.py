from typing import TypedDict
from langgraph.graph import StateGraph, END

class GraphMatState(TypedDict):
    grid_resolution: float
    material_spec: str
    is_verified: bool

def validate_specs(state: GraphMatState):
    if state['grid_resolution'] > 0 and state['material_spec']:
        return {'is_verified': True}
    return {'is_verified': False}

graph = StateGraph(GraphMatState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()