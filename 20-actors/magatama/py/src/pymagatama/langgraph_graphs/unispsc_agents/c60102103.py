from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BookProcurementState(TypedDict):
    isbn: str
    title: str
    verified: bool
    compliance_report: str

def validate_isbn(state: BookProcurementState) -> BookProcurementState:
    # Logic to verify ISBN format and database check
    state['verified'] = len(state['isbn']) >= 10
    state['compliance_report'] = 'ISBN Format Validated' if state['verified'] else 'Invalid ISBN'
    return state

def approve_procurement(state: BookProcurementState) -> BookProcurementState:
    state['compliance_report'] += ' | Procurement Approved'
    return state

graph = StateGraph(BookProcurementState)
graph.add_node('validate', validate_isbn)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()