from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DopplerState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_specs(state: DopplerState):
    errors = []
    if not state['specs'].get('certification'):
        errors.append('Missing mandatory medical certification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_validation(state: DopplerState):
    return 'approved' if state['approved'] else END

graph = StateGraph(DopplerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
