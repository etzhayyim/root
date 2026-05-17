from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    book_isbn: str
    curriculum_level: str
    is_verified: bool

def validate_resource(state: ProcurementState):
    state['is_verified'] = len(state['book_isbn']) >= 10
    return state

def route_procurement(state: ProcurementState):
    return 'process' if state['is_verified'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_resource)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()