from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class StrappingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_tensile_strength(state: StrappingState):
    strength = state['spec_data'].get('tensile_strength', 0)
    if strength < 500:
        return {'validation_passed': False, 'errors': ['Insufficient tensile strength']}
    return {'validation_passed': True}

def check_material_compliance(state: StrappingState):
    material = state['spec_data'].get('material', '')
    if material not in ['Steel', 'Stainless Steel']:
        return {'validation_passed': False, 'errors': ['Unsupported material type']}
    return {'validation_passed': True}

graph = StateGraph(StrappingState)
graph.add_node('validate_strength', validate_tensile_strength)
graph.add_node('validate_material', check_material_compliance)
graph.set_entry_point('validate_strength')
graph.add_edge('validate_strength', 'validate_material')
graph.add_edge('validate_material', END)
app = graph.compile()