from typing import TypedDict
from langgraph.graph import StateGraph, END

class RailState(TypedDict):
    spec: dict
    validated: bool

def validate_rail_specs(state: RailState):
    s = state['spec']
    valid = ('width' in s and s['width'] == 35) and ('material' in s)
    return {'validated': valid}

graph = StateGraph(RailState)
graph.add_node('validator', validate_rail_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()
