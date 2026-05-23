from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    safety_cleared: bool
    is_dual_use: bool

def validate_purity(state: ChemicalState):
    return {"safety_cleared": state['purity'] > 99.9}

def check_export_controls(state: ChemicalState):
    return {"is_dual_use": state['purity'] > 99.99}

graph = StateGraph(ChemicalState)
graph.add_node("validate", validate_purity)
graph.add_node("export_check", check_export_controls)
graph.set_entry_point("validate")
graph.add_edge("validate", "export_check")
graph.add_edge("export_check", END)
graph = graph.compile()
