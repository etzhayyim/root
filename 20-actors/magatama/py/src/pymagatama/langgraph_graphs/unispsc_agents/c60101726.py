from typing import TypedDict
from langgraph.graph import StateGraph, END

class DocState(TypedDict):
    document_path: str
    is_validated: bool
    revision_check: bool

def validate_format(state: DocState):
    # Simulate PDF/EPUB validation logic
    return {'is_validated': state['document_path'].endswith('.pdf')}

def check_revision(state: DocState):
    # Simulate metadata parsing for document versions
    return {'revision_check': True}

graph = StateGraph(DocState)
graph.add_node('validate', validate_format)
graph.add_node('revision', check_revision)
graph.set_entry_point('validate')
graph.add_edge('validate', 'revision')
graph.add_edge('revision', END)
app = graph.compile()
