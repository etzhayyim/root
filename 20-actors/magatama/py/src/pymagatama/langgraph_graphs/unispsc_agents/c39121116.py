from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchgearState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_electrical_specs(state: SwitchgearState):
    errors = []
    if state['spec_data'].get('voltage', 0) > 1000:
        errors.append('Voltage exceeds low-voltage threshold')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SwitchgearState)
graph.add_node('validate', validate_electrical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()