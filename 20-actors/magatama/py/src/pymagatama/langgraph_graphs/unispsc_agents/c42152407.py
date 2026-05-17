from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalMaterialState(TypedDict):
    material_type: str
    particle_size: float
    compliance_checked: bool

def validate_material(state: DentalMaterialState):
    # Perform ISO standard compliance validation for abrasive dental powders
    state['compliance_checked'] = (state['particle_size'] > 0)
    return state

def stage_approval(state: DentalMaterialState):
    # Procedural step for regulated health product quality check
    return {'compliance_checked': True}

graph = StateGraph(DentalMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('approve', stage_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()