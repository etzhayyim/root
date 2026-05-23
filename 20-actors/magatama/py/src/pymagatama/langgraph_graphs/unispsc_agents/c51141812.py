from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    purity: float
    temp_log: list
    is_compliant: bool

def validate_purity(state: PharmaState):
    state['is_compliant'] = state['purity'] >= 99.5
    return state

def check_cold_chain(state: PharmaState):
    state['is_compliant'] = state['is_compliant'] and all(2 <= t <= 8 for t in state['temp_log'])
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cold_chain', check_cold_chain)
graph.add_edge('validate_purity', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph.set_entry_point('validate_purity')
