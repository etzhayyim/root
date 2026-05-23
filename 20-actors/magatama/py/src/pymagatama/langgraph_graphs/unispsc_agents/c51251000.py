from typing import TypedDict
from langgraph.graph import StateGraph, END

class MetaboliteState(TypedDict):
    purity: float
    temp_compliance: bool
    verified: bool

def validate_purity(state: MetaboliteState):
    state['verified'] = state['purity'] >= 0.99
    return state

def check_cold_chain(state: MetaboliteState):
    state['temp_compliance'] = True
    return state

graph = StateGraph(MetaboliteState)
graph.add_node("validate", validate_purity)
graph.add_node("cold_chain", check_cold_chain)
graph.set_entry_point("validate")
graph.add_edge("validate", "cold_chain")
graph.add_edge("cold_chain", END)
graph = graph.compile()
