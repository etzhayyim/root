from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OvershoeState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_material(state: OvershoeState):
    errors = []
    if not state['spec_data'].get('waterproof'):
        errors.append('Missing waterproof rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def finalize_spec(state: OvershoeState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(OvershoeState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_spec)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
