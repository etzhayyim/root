from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThrombinState(TypedDict):
    purity: float
    temp_celsius: float
    status: str

def validate_purity(state: ThrombinState):
    if state['purity'] < 0.95: return {'status': 'rejected'}
    return {'status': 'purity_validated'}

def check_cold_chain(state: ThrombinState):
    if state['temp_celsius'] > -20.0: return {'status': 'expired'}
    return {'status': 'ready'}

graph = StateGraph(ThrombinState)
graph.add_node("validate", validate_purity)
graph.add_node("cold_chain", check_cold_chain)
graph.set_entry_point("validate")
graph.add_edge("validate", "cold_chain")
graph.add_edge("cold_chain", END)
graph = graph.compile()
