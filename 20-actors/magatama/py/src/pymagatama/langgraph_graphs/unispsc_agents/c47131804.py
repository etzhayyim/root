from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningAgentState(TypedDict):
    product_name: str
    ammonia_level: float
    has_sds: bool
    is_compliant: bool

def validate_safety(state: CleaningAgentState) -> CleaningAgentState:
    if state['ammonia_level'] > 10.0:
        state['is_compliant'] = False
    else:
        state['is_compliant'] = state['has_sds']
    return state

def route_procurement(state: CleaningAgentState) -> str:
    return 'APPROVED' if state['is_compliant'] else 'REJECTED'

graph = StateGraph(CleaningAgentState)
graph.add_node('validate', validate_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
