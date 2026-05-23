from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_gmp(state: ProcurementState):
    print('Validating GMP certification and assay purity...')
    state['is_approved'] = 'GMP' in state['compliance_docs']
    return state

def route_procurement(state: ProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gmp)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
