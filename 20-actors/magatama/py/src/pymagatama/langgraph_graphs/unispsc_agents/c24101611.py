from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SlingState(TypedDict):
    load_capacity: float
    certification_valid: bool
    inspection_result: str

def validate_load_capacity(state: SlingState):
    state['certification_valid'] = state['load_capacity'] > 0
    return 'checked'

def check_compliance(state: SlingState):
    state['inspection_result'] = 'APPROVED' if state['certification_valid'] else 'REJECTED'
    return 'verified'

graph = StateGraph(SlingState)
graph.add_node('validator', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validator', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validator')
graph = graph.compile()
