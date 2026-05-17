from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    product_id: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: DentalState):
    required = ['ISO_4049', 'Biocompatibility']
    state['is_approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def route_by_approval(state: DentalState):
    return 'approve' if state['is_approved'] else 'reject'

graph = StateGraph(DentalState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', 'approve' if True else 'reject')
graph.set_entry_point('validate')
graph.add_edge('approve', END)
graph.add_edge('reject', END)
app = graph.compile()