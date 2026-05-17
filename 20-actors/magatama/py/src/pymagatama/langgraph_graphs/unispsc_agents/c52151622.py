from langgraph.graph import StateGraph, END
from typing import TypedDict

class DecoratingGunState(TypedDict):
    material_safety_cert: bool
    nozzle_count: int
    is_approved: bool

def validate_specs(state: DecoratingGunState):
    state['is_approved'] = state['material_safety_cert'] and state['nozzle_count'] > 0
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(DecoratingGunState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()