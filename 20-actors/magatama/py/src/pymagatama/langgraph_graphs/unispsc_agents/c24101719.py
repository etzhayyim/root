from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ConveyorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ConveyorState):
    errors = []
    if not state['spec_data'].get('bristle_material'):
        errors.append('Missing bristle material specification')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_verification(state: ConveyorState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(ConveyorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()