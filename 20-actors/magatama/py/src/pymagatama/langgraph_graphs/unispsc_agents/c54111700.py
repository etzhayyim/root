from typing import TypedDict
from langgraph.graph import StateGraph, END

class WatchPartState(TypedDict):
    part_id: str
    spec_sheet: dict
    approved: bool

def validate_specs(state: WatchPartState):
    # Simulate CAD and material validation logic
    tolerance = state['spec_sheet'].get('tolerance', 0.05)
    approved = tolerance <= 0.01
    return {'approved': approved}

graph = StateGraph(WatchPartState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()