from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WindowProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WindowProcurementState):
    errors = []
    if state['spec_data'].get('u_value', 0) > 2.0:
        errors.append('Thermal insulation performance exceeds maximum threshold.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(WindowProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()