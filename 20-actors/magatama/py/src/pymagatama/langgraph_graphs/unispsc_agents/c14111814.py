from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from operator import add

class FileProcState(TypedDict):
    doc_count: int
    validation_errors: Annotated[Sequence[str], add]
    is_archivable: bool

def validate_filing_compliance(state: FileProcState):
    # Simple business logic: check if doc_count allows for standard filing
    is_valid = state['doc_count'] > 0
    return {'is_archivable': is_valid}

def categorize_document(state: FileProcState):
    # Simulate classification logic
    if state['doc_count'] > 1000:
        return {'validation_errors': ['Bulk storage handling required']}
    return {'validation_errors': []}

graph = StateGraph(FileProcState)
graph.add_node('validate', validate_filing_compliance)
graph.add_node('categorize', categorize_document)
graph.set_entry_point('validate')
graph.add_edge('validate', 'categorize')
graph.add_edge('categorize', END)
graph = graph.compile()
