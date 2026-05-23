from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    part_id: str
    material_spec: dict
    tolerance_check: bool
    approved: bool

def validate_specs(state: CastState):
    # Simulate CAD/Spec validation logic
    tolerance = state['material_spec'].get('tolerance', 0.05)
    return {'tolerance_check': tolerance <= 0.1}

def approval_step(state: CastState):
    return {'approved': state['tolerance_check']}

graph = StateGraph(CastState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
