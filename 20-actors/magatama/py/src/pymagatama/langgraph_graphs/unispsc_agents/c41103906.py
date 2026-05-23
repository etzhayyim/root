from typing import TypedDict
from langgraph.graph import StateGraph, END

class CentrifugeState(TypedDict):
    specs: dict
    validation_errors: list[str]
    is_approved: bool

def validate_cooling_specs(state: CentrifugeState):
    errors = []
    if state['specs'].get('temp_range', 0) > 4:
        errors.append('Temperature range exceeds required clinical limit of 4C.')
    return {'validation_errors': errors}

def approval_check(state: CentrifugeState):
    return 'APPROVED' if not state['validation_errors'] else 'REJECTED'

graph = StateGraph(CentrifugeState)
graph.add_node('validate', validate_cooling_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
