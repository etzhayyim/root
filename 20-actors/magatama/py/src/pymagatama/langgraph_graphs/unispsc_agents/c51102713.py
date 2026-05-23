from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_status: bool
    is_compliant: bool

def validate_purity(state: ProcurementState):
    return {'is_compliant': state['purity'] >= 9.0 and state['gmp_status']}

def router(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
