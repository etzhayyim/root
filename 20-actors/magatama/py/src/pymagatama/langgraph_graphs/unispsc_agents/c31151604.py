from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChainState(TypedDict):
    load_requirement: float
    safety_factor: int
    cert_provided: bool
    is_approved: bool

def validate_load(state: ChainState) -> ChainState:
    if state['load_requirement'] > 0 and state['safety_factor'] >= 4:
        state['is_approved'] = True
    return state

def check_certification(state: ChainState) -> ChainState:
    if not state.get('cert_provided', False):
        state['is_approved'] = False
    return state

graph = StateGraph(ChainState)
graph.add_node("validate", validate_load)
graph.add_node("certify", check_certification)
graph.set_entry_point("validate")
graph.add_edge("validate", "certify")
graph.add_edge("certify", END)
graph = graph.compile()