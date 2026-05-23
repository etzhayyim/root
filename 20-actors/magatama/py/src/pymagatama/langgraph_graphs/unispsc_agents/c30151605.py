from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrainState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_drain_specs(state: DrainState):
    errors = []
    if 'connection_diameter' not in state['spec_data']:
        errors.append('Missing connection diameter')
    if 'material' not in state['spec_data']:
        errors.append('Missing material specification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(DrainState)
graph.add_node('validate', validate_drain_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
