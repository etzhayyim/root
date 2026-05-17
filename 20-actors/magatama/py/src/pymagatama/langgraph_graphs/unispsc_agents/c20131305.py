from typing import TypedDict
from langgraph.graph import StateGraph, END

class MechanismState(TypedDict):
    spec_data: dict
    validation_score: float
    compliance_risk: bool

def validate_load_capacity(state: MechanismState):
    capacity = state['spec_data'].get('load_capacity_rating', 0)
    return {'validation_score': 1.0 if capacity > 0 else 0.0}

def check_export_controls(state: MechanismState):
    material = state['spec_data'].get('material_composition')
    risk = 'high_strength_alloy' in material.lower()
    return {'compliance_risk': risk}

graph = StateGraph(MechanismState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_export_controls)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')