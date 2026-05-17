from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class UVProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_uv_specs(state: UVProcurementState):
    errors = []
    if state['spec_data'].get('Wavelength_nm', 0) < 200:
        errors.append('Wavelength below safety threshold')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def safety_compliance_check(state: UVProcurementState):
    return {'validation_passed': True}

graph = StateGraph(UVProcurementState)
graph.add_node('validate', validate_uv_specs)
graph.add_node('compliance', safety_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()