from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BeamState(TypedDict):
    load_tests: List[float]
    is_compliant: bool
    error_log: List[str]

def validate_structural_integrity(state: BeamState):
    state['is_compliant'] = all(load > 1500 for load in state['load_tests'])
    if not state['is_compliant']:
        state['error_log'].append('Structural test failure: load below threshold')
    return state

builder = StateGraph(BeamState)
builder.add_node('validation', validate_structural_integrity)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()