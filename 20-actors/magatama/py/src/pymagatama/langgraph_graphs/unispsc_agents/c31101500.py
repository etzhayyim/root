from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DieCastState(TypedDict):
    part_id: str
    specs: dict
    approved: bool

def validate_specs(state: DieCastState):
    # Simulate CAD/Spec validation for die cast tolerances
    tolerance = state['specs'].get('tolerance', 0.05)
    approved = tolerance <= 0.1
    return {'approved': approved}

graph = StateGraph(DieCastState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compiled_graph = graph.compile()