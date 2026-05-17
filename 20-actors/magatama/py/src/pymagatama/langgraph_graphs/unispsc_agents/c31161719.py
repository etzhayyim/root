from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwivelNutState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_material(state: SwivelNutState):
    material = state['spec_data'].get('material_specification')
    errors = state.get('validation_errors', [])
    if not material:
        errors.append('Missing material specification')
    return {'validation_errors': errors}

def check_compliance(state: SwivelNutState):
    is_compliant = len(state.get('validation_errors', [])) == 0
    return {'is_compliant': is_compliant}

graph = StateGraph(SwivelNutState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()