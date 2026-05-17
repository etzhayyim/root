from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LimeState(TypedDict):
    quality_score: float
    inspection_passed: bool
    transit_path: List[str]

def quality_check(state: LimeState):
    state['inspection_passed'] = state['quality_score'] > 0.8
    return state

def route_logistics(state: LimeState):
    state['transit_path'] = ['farm', 'cold_storage', 'distributor']
    return state

graph = StateGraph(LimeState)
graph.add_node('qc', quality_check)
graph.add_node('logistics', route_logistics)
graph.add_edge('qc', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('qc')
graph = graph.compile()