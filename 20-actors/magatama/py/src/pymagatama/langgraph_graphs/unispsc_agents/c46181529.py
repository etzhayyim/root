from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClothingState(TypedDict):
    material_specs: dict
    compliance_validated: bool
    thermal_rating: float

def validate_insulation(state: ClothingState):
    state['compliance_validated'] = state['thermal_rating'] >= 2.0
    return 'validated' if state['compliance_validated'] else 'rejected'

def finalize_procurement(state: ClothingState): return {'status': 'approved'}

graph = StateGraph(ClothingState)
graph.add_node('validate', validate_insulation)
graph.add_node('final', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()