from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeatState(TypedDict):
    temp_log: list[float]
    is_safe: bool
    cert_valid: bool
    approved: bool

def validate_cold_chain(state: MeatState) -> MeatState:
    state['is_safe'] = all(t < 5.0 for t in state['temp_log'])
    return state

def check_compliance(state: MeatState) -> MeatState:
    state['approved'] = state['is_safe'] and state['cert_valid']
    return state

graph = StateGraph(MeatState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()