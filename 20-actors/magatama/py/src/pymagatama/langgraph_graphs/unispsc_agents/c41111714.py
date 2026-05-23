from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LoupeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: LoupeState):
    errors = []
    if not state['spec_data'].get('medical_device_certification'):
        errors.append('Missing mandatory medical certification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LoupeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
