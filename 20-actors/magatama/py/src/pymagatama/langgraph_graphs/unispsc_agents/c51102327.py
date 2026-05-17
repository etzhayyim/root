from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: list
    verified: bool

def validate_purity(state: PharmState):
    state['verified'] = state['purity_level'] >= 0.99
    return state

def check_cold_chain(state: PharmState):
    if all(temp <= 25 for temp in state['temp_log']):
        return state
    state['verified'] = False
    return state

graph = StateGraph(PharmState)
graph.add_node("validate", validate_purity)
graph.add_node("cold_chain", check_cold_chain)
graph.set_entry_point("validate")
graph.add_edge("validate", "cold_chain")
graph.add_edge("cold_chain", END)
app = graph.compile()