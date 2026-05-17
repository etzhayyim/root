from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProduceState(TypedDict):
    quality_score: float
    inspection_passed: bool
    logistics_status: str

def validate_quality(state: ProduceState):
    state['inspection_passed'] = state['quality_score'] >= 0.8
    return state

def check_logistics(state: ProduceState):
    state['logistics_status'] = 'Cold Chain Verified' if state['inspection_passed'] else 'Rejected'
    return state

graph = StateGraph(ProduceState)
graph.add_node('inspection', validate_quality)
graph.add_node('logistics', check_logistics)
graph.set_entry_point('inspection')
graph.add_edge('inspection', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()