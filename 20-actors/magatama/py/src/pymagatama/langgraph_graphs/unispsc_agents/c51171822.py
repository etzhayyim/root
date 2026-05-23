from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    api_name: str
    purity: float
    gmp_status: bool
    is_compliant: bool

def validate_purity(state: PharmaState) -> PharmaState:
    state['is_compliant'] = state['purity'] >= 99.0 and state['gmp_status']
    return state

def log_procurement(state: PharmaState):
    print(f"Processing {state['api_name']} - Compliance: {state['is_compliant']}")

graph = StateGraph(PharmaState)
graph.add_node("validate", validate_purity)
graph.add_node("log", log_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "log")
graph.add_edge("log", END)
graph = graph.compile()
