from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AddressBookState(TypedDict):
    specifications: dict
    is_valid: bool
    validation_errors: List[str]

def validate_specs(state: AddressBookState):
    errors = []
    if 'material' not in state['specifications']: errors.append('Missing material')
    if 'size' not in state['specifications']: errors.append('Missing size')
    return {'is_valid': len(errors) == 0, 'validation_errors': errors}

def approval_step(state: AddressBookState):
    return {'is_valid': True}

graph = StateGraph(AddressBookState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
