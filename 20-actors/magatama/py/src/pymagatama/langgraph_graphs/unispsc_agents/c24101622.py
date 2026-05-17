from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraneState(TypedDict):
    capacity: float
    inspection_passed: bool
    approved: bool

def validate_specs(state: CraneState):
    state['inspection_passed'] = state['capacity'] > 0
    return {'inspection_passed': state['inspection_passed']}

def approval_check(state: CraneState):
    state['approved'] = state['inspection_passed']
    return 'APPROVED' if state['approved'] else 'REJECTED'

graph = StateGraph(CraneState)
graph.add_node('validation', validate_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()