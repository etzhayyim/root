from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: FreezerState):
    errors = []
    if state['spec_data'].get('energy_rating') not in ['A', 'A+', 'A++']:
        errors.append('Energy efficiency rating insufficient')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def approval_step(state: FreezerState):
    print(f'Approval status: {state['is_approved']}')
    return state

graph = StateGraph(FreezerState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
