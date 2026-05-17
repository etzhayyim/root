from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    gmp_certified: bool
    is_compliant: bool

def validate_purity(state: ProcurementState):
    state['is_compliant'] = state['purity_level'] >= 99.0 and state['gmp_certified']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()