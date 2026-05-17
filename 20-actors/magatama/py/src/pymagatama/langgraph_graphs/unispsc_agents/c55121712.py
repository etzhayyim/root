from typing import TypedDict
from langgraph.graph import StateGraph, END

class SignageState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: list

def validate_specs(state: SignageState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material')
    if 'contrast_ratio' in state['specs'] and state['specs']['contrast_ratio'] < 4.5:
        errors.append('Insufficient contrast ratio')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(SignageState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()