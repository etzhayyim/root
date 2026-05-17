from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HexKeyState(TypedDict):
    material: str
    size: str
    compliance: str
    is_approved: bool

def validate_spec(state: HexKeyState):
    is_compliant = "ISO" in state["compliance"] and state["material"] != "Low-grade Steel"
    return {"is_approved": is_compliant}

def approval_check(state: HexKeyState):
    return "approved" if state["is_approved"] else "rejected"

graph = StateGraph(HexKeyState)
graph.add_node("validate", validate_spec)
graph.add_edge("validate", END)
graph.set_entry_point("validate")