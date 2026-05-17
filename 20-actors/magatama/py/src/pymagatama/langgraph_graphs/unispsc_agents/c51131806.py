from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    safety_compliant: bool
    hazard_check: bool

def validate_purity(state: ChemicalState):
    return {"safety_compliant": state["purity"] >= 99.0}

def check_hazards(state: ChemicalState):
    return {"hazard_check": True}

graph = StateGraph(ChemicalState)
graph.add_node("validate", validate_purity)
graph.add_node("hazards", check_hazards)
graph.add_edge("validate", "hazards")
graph.add_edge("hazards", END)
graph.set_entry_point("validate")
graph = graph.compile()