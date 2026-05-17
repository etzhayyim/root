from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: list
    verified: bool

def validate_purity(state: ProcurementState):
    state['verified'] = state['purity_level'] >= 0.99
    return state

def check_storage(state: ProcurementState):
    state['verified'] = state['verified'] and all(t < 8.0 for t in state['temp_log'])
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_storage', check_storage)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_storage')
graph.add_edge('check_storage', END)
graph = graph.compile()