from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BookmarkState(TypedDict):
    material: str
    quantity: int
    is_branded: bool
    validation_errors: List[str]

def validate_bookmark_spec(state: BookmarkState) -> BookmarkState:
    errors = []
    if state['quantity'] <= 0:
        errors.append('Quantity must be positive')
    if state['material'] not in ['paper', 'fabric', 'metal', 'plastic']:
        errors.append('Invalid material type')
    return {'validation_errors': errors}

workflow = StateGraph(BookmarkState)
workflow.add_node('validate', validate_bookmark_spec)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()