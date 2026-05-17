from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    gmp_valid: bool
    compliance_check: bool

def validate_purity(state: PharmaState):
    state['compliance_check'] = state['purity'] >= 99.0
    return state

def check_gmp(state: PharmaState):
    return {"compliance_check": state['gmp_valid']}

graph = StateGraph(PharmaState)
graph.add_node("validate", validate_purity)
graph.add_node("check_gmp", check_gmp)
graph.set_entry_point("validate")
graph.add_edge("validate", "check_gmp")
graph.add_edge("check_gmp", END)
graph = graph.compile()