from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_number: str
    purity_level: float
    temp_log: list
    is_compliant: bool

def validate_purity(state: PharmState):
    state['is_compliant'] = state['purity_level'] >= 99.0
    return state

def check_cold_chain(state: PharmState):
    if any(t > 8 for t in state['temp_log']):
        state['is_compliant'] = False
    return state

graph = StateGraph(PharmState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cold_chain', check_cold_chain)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph = graph.compile()