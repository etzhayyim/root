from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CableTieState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_material(state: CableTieState):
    material = state['spec_data'].get('material_type')
    if not material:
        state['validation_errors'].append('Material type missing')
    return state

def check_strength(state: CableTieState):
    if state['spec_data'].get('tensile_strength_rating', 0) < 50:
        state['validation_errors'].append('Insufficient tensile strength for industrial use')
    return state

graph = StateGraph(CableTieState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_strength', check_strength)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_strength')
graph.add_edge('check_strength', END)
graph = graph.compile()