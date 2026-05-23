from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    material_spec: dict
    validation_results: dict
    is_approved: bool

def validate_composition(state: CastingState):
    purity = state['material_spec'].get('purity', 0)
    return {'validation_results': {'composition': purity >= 99.9}}

def check_dimensions(state: CastingState):
    tol = state['material_spec'].get('tolerance', 1.0)
    return {'validation_results': {'dimensions': tol <= 0.05}}

graph = StateGraph(CastingState)
graph.add_node('validate_material', validate_composition)
graph.add_node('verify_dimensional', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'verify_dimensional')
graph.add_edge('verify_dimensional', END)
graph = graph.compile()
