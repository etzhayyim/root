from typing import TypedDict
from langgraph.graph import StateGraph, END

class BookState(TypedDict):
    isbn: str
    is_verified: bool
    metadata: dict

def validate_metadata(state: BookState):
    print(f"Validating ISBN: {state['isbn']}")
    return {"is_verified": True if state['isbn'] else False}

def update_catalog(state: BookState):
    print("Updating library procurement catalog.")
    return {"metadata": {"status": "cataloged"}}

graph = StateGraph(BookState)
graph.add_node("validate", validate_metadata)
graph.add_node("catalog", update_catalog)
graph.set_entry_point("validate")
graph.add_edge("validate", "catalog")
graph.add_edge("catalog", END)
graph = graph.compile()
