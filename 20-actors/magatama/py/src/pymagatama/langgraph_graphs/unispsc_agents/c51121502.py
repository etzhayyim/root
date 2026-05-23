from typing import TypedDict
from langgraph.graph import StateGraph, END

class DigoxinState(TypedDict):
    batch_number: str
    purity_level: float
    storage_temp: float
    is_compliant: bool

def validate_purity(state: DigoxinState):
    state['is_compliant'] = state['purity_level'] >= 0.99
    return state

def check_cold_chain(state: DigoxinState):
    state['is_compliant'] = state['is_compliant'] and (2 <= state['storage_temp'] <= 8)
    return state

graph = StateGraph(DigoxinState)
graph.add_node('validate', validate_purity)
graph.add_node('cold_chain', check_cold_chain)
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph.set_entry_point('validate')
graph = graph.compile()
