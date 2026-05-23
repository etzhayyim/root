from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class GeneticsBookState(TypedDict):
    isbn: str
    title: str
    is_verified: bool
    validation_log: Annotated[list, operator.add]

def validate_isbn(state: GeneticsBookState):
    # Simple validation logic placeholder
    valid = len(state['isbn']) >= 10
    return {"is_verified": valid, "validation_log": [f"ISBN validation: {valid}"]}

def catalog_book(state: GeneticsBookState):
    return {"validation_log": [f"Book {state.get('title')} added to catalog"]}

builder = StateGraph(GeneticsBookState)
builder.add_node("validate", validate_isbn)
builder.add_node("catalog", catalog_book)
builder.set_entry_point("validate")
builder.add_edge("validate", "catalog")
builder.add_edge("catalog", END)
graph = builder.compile()
