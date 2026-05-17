from typing import TypedDict
from langgraph.graph import StateGraph, END

class BracketState(TypedDict):
    material_specs: dict
    compliance_check: bool
    approved: bool

def validate_material(state: BracketState):
    # Simulate material property validation logic
    state['compliance_check'] = state['material_specs'].get('tensile_strength', 0) > 250
    return state

def approval_step(state: BracketState):
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(BracketState)
graph.add_node('validate', validate_material)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()