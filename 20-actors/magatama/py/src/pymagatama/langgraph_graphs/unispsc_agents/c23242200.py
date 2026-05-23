from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GearMachiningState(TypedDict):
    specs: dict
    validation_errors: List[str]
    compliance_cleared: bool

def validate_specs(state: GearMachiningState):
    required = ['precision_tolerance', 'max_diameter']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_errors': errors}

def check_export_compliance(state: GearMachiningState):
    is_cleared = state['specs'].get('export_control_classification_number') is not None
    return {'compliance_cleared': is_cleared}

graph = StateGraph(GearMachiningState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
