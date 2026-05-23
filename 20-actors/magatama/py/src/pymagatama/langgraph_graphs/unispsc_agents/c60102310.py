from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BookState(TypedDict):
    isbn: str
    title: str
    is_verified: bool
    metadata: dict

def validate_metadata(state: BookState):
    is_valid = len(state['isbn']) >= 10 and state['title'] != ""
    return {"is_verified": is_valid}

def process_procurement(state: BookState):
    return {"metadata": {"status": "ready_for_order", "action": "catalog_entry"}}

graph = StateGraph(BookState)
graph.add_node("validate", validate_metadata)
graph.add_node("process", process_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph = graph.compile()
