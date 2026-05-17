from typing import TypedDict
from langgraph.graph import StateGraph, END

class DocumentationState(TypedDict):
    doc_type: str
    is_compliant: bool
    revision: int

def validate_format(state: DocumentationState):
    state['is_compliant'] = state.get('doc_type') in ['PDF', 'HTML', 'Markdown']
    return state

def update_version(state: DocumentationState):
    state['revision'] += 1
    return state

graph = StateGraph(DocumentationState)
graph.add_node('validate', validate_format)
graph.add_node('update', update_version)
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
graph.set_entry_point('validate')
graph = graph.compile()