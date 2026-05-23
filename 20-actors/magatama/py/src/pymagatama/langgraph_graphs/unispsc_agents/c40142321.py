from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_pressure_rating(state: PipeState):
    rating = state['spec_data'].get('pressure_psi', 0)
    if rating < 150: return {'validated': False, 'error': 'Below industrial minimum'}
    return {'validated': True}

def check_material_compliance(state: PipeState):
    if state['spec_data'].get('material') not in ['Stainless Steel', 'Carbon Steel']:
        return {'validated': False, 'error': 'Non-standard metallurgy'}
    return {'validated': True}

graph = StateGraph(PipeState)
graph.add_node('pressure_check', validate_pressure_rating)
graph.add_node('material_check', check_material_compliance)
graph.set_entry_point('pressure_check')
graph.add_edge('pressure_check', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
