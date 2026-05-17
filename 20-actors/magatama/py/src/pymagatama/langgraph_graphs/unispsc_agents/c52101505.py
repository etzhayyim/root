from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RugState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: RugState):
    errors = []
    if 'fire_retardancy_standard' not in state['spec_data']:
        errors.append('Missing mandatory fire safety cert')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def finalize_procurement(state: RugState):
    return {'validation_passed': True}

graph = StateGraph(RugState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()