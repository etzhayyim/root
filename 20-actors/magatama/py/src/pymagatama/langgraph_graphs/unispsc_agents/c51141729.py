from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity: float
    gmp_verified: bool
    compliant: bool

def validate_purity(state: ProcurementState):
    is_pure = state['purity'] >= 99.0
    return {'compliant': is_pure and state['gmp_verified']}

def check_compliance(state: ProcurementState):
    return 'compliant' if state['compliant'] else 'non-compliant'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
