from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    purity: float
    has_coa: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0
    return state

def check_documentation(state: ProcurementState):
    if not state.get('has_coa', False):
        state['is_approved'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_docs', check_documentation)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_docs')
graph.add_edge('check_docs', END)
graph = graph.compile()
