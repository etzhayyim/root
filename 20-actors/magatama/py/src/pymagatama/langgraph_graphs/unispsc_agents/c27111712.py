from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PullerState(TypedDict):
    spec_data: dict
    validation_ok: bool
    error_log: List[str]

def validate_puller(state: PullerState):
    errors = []
    if state['spec_data'].get('pulling_capacity_tons', 0) <= 0:
        errors.append('Invalid capacity')
    return {'validation_ok': len(errors) == 0, 'error_log': errors}

graph = StateGraph(PullerState)
graph.add_node('validate', validate_puller)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
