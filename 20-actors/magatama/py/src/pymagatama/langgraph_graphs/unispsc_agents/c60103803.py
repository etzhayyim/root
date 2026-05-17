from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HistoryBookState(TypedDict):
    book_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_metadata(state: HistoryBookState):
    errors = []
    if 'ISBN' not in state['book_data']: errors.append('Missing ISBN')
    if 'publication_year' not in state['book_data']: errors.append('Missing Publication Year')
    return {'validation_errors': errors}

def approval_check(state: HistoryBookState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(HistoryBookState)
graph.add_node('validate', validate_metadata)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()