from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    lubricant_id: str
    viscosity: float
    safety_score: float
    approval_status: bool

def validate_viscosity(state: LubricantState) -> dict:
    return {"approval_status": state["viscosity"] > 10.0}

def check_safety(state: LubricantState) -> dict:
    return {"safety_score": 0.95 if state["approval_status"] else 0.5}

graph = StateGraph(LubricantState)
graph.add_node("validate", validate_viscosity)
graph.add_node("safety_check", check_safety)
graph.set_entry_point("validate")
graph.add_edge("validate", "safety_check")
graph.add_edge("safety_check", END)
compiled_graph = graph.compile()