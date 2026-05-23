from langgraph.graph import StateGraph, END
from typing import TypedDict

class ChemicalState(TypedDict):
    purity: float
    has_sds: bool
    compliant: bool

def validate_purity(state: ChemicalState):
    return {"compliant": state['purity'] >= 0.99}

def check_sds(state: ChemicalState):
    return {"compliant": state['has_sds']}

graph = StateGraph(ChemicalState)
graph.add_node("validate", validate_purity)
graph.add_node("check", check_sds)
graph.add_edge("validate", "check")
graph.add_edge("check", END)
graph.set_entry_point("validate")
graph = graph.compile()
