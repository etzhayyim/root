from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    purity_level: float
    has_coa: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity_level'] >= 99.0
    return 'check_docs' if state['is_approved'] else END

def check_docs(state: ProcurementState):
    state['is_approved'] = state['has_coa']
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('check_docs', check_docs)
graph.set_entry_point('validate')
graph.add_edge('check_docs', END)
graph.compile()
