from langgraph.graph import StateGraph, END
from typing import TypedDict

class PressureTransmitterState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: PressureTransmitterState):
    errors = []
    if state['spec_data'].get('accuracy') is None:
        errors.append('Missing Accuracy Class')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_verification(state: PressureTransmitterState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(PressureTransmitterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

# Compilation
app = graph.compile()
