from typing import TypedDict
from langgraph.graph import StateGraph, END

class DressingState(TypedDict):
    product_id: str
    is_sterile: bool
    expiry_date: str
    quality_check_passed: bool

def validate_sterility(state: DressingState):
    return {"quality_check_passed": state.get("is_sterile", False)}

def log_procurement(state: DressingState):
    print(f"Processing dressing {state['product_id']} for distribution.")
    return {"quality_check_passed": True}

graph = StateGraph(DressingState)
graph.add_node("validate", validate_sterility)
graph.add_node("log", log_procurement)
graph.add_edge("validate", "log")
graph.add_edge("log", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
