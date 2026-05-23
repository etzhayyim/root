from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireState(TypedDict):
    spec_sheet: dict
    validated: bool
    safety_check: bool

def validate_asbestos_safety(state: WireState):
    content = state['spec_sheet'].get('asbestos_content', 0)
    return {'safety_check': content < 0.1}

def validate_electrical_specs(state: WireState):
    temp_rating = state['spec_sheet'].get('temp_rating', 0)
    return {'validated': temp_rating >= 200}

graph = StateGraph(WireState)
graph.add_node('safety', validate_asbestos_safety)
graph.add_node('electrical', validate_electrical_specs)
graph.set_entry_point('safety')
graph.add_edge('safety', 'electrical')
graph.add_edge('electrical', END)
graph = graph.compile()
