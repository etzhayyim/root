from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlackberryState(TypedDict):
    quality_score: float
    inspection_passed: bool
    compliant: bool

def validate_quality(state: BlackberryState):
    state['inspection_passed'] = state['quality_score'] > 85.0
    return state

def check_compliance(state: BlackberryState):
    state['compliant'] = state['inspection_passed']
    return state

graph = StateGraph(BlackberryState)
graph.add_node('inspection', validate_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('inspection')
graph.add_edge('inspection', 'compliance')
graph.add_edge('compliance', END)
graph.compile()