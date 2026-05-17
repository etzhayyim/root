from langgraph.graph import StateGraph, END
from typing import TypedDict
class DictState(TypedDict):
    title: str
    isbn: str
    is_verified: bool
def validate_metadata(state: DictState):
    return {"is_verified": bool(state["isbn"] and len(state["title"]) > 0)}
def check_format(state: DictState):
    return {"is_verified": state["is_verified"] and "digital" in state["title"].lower()}
graph = StateGraph(DictState)
graph.add_node("validate", validate_metadata)
graph.add_node("check", check_format)
graph.set_entry_point("validate")
graph.add_edge("validate", "check")
graph.add_edge("check", END)
graph = graph.compile()