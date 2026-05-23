from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoringMachineState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: BoringMachineState):
    errors = []
    if state['spec_data'].get('spindle_diameter', 0) < 50:
        errors.append('Spindle diameter below industrial standard')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: BoringMachineState):
    return 'compliant' if state['is_compliant'] else 'review'

graph = StateGraph(BoringMachineState)
graph.add_node('validation', validate_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
