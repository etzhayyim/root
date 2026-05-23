from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SignalCableState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: SignalCableState):
    errors = []
    if 'voltage_rating' not in state['spec_data']:
        errors.append('Missing voltage rating')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

graph = StateGraph(SignalCableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
