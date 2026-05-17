from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BookProcurementState(TypedDict):
    title: str
    age_group: str
    safety_certs: List[str]
    spec_approved: bool

def validate_safety(state: BookProcurementState):
    required = ['Non-toxic Ink', 'Consumer Safety Standard']
    state['spec_approved'] = all(item in state['safety_certs'] for item in required)
    return state

def route_by_spec(state: BookProcurementState):
    return 'process' if state['spec_approved'] else 'reject'

graph = StateGraph(BookProcurementState)
graph.add_node('validate', validate_safety)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()