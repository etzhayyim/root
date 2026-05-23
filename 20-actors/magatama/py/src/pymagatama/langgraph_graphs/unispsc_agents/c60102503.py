from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DocState(TypedDict):
    content: str
    validation_errors: List[str]
    is_approved: bool

def validate_content(state: DocState):
    errors = []
    if not state['content']:
        errors.append('Content is empty')
    return {'validation_errors': errors}

def approve_doc(state: DocState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(DocState)
graph.add_node('validator', validate_content)
graph.add_node('approver', approve_doc)
graph.add_edge('validator', 'approver')
graph.add_edge('approver', END)
graph.set_entry_point('validator')
graph = graph.compile()
