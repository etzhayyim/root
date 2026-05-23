from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ThoracentesisState(TypedDict):
    needle_spec: dict
    validation_errors: List[str]
    is_approved: bool

def validate_medical_spec(state: ThoracentesisState):
    errors = []
    if 'gauge_size' not in state['needle_spec']:
        errors.append('Missing mandatory gauge size')
    if state.get('needle_spec', {}).get('sterilization') != 'ethylene_oxide':
        errors.append('Invalid sterilization method')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(ThoracentesisState)
graph.add_node('validate', validate_medical_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
