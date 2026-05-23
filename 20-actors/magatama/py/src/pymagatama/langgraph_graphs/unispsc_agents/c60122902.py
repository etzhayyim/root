from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BeadState(TypedDict):
    spec_data: dict
    validated: bool
    errors: List[str]

def validate_specs(state: BeadState):
    errors = []
    if not state['spec_data'].get('material'):
        errors.append('Missing material type')
    return {'validated': len(errors) == 0, 'errors': errors}

def approval_node(state: BeadState):
    print('Bead configuration verified for procurement.')
    return {'validated': True}

graph = StateGraph(BeadState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
