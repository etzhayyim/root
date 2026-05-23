from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BradState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: BradState):
    errors = []
    if not state['spec_data'].get('gauge'):
        errors.append('Missing gauge dimension')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: BradState):
    return 'pass' if state['validation_passed'] else 'fail'

graph = StateGraph(BradState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
