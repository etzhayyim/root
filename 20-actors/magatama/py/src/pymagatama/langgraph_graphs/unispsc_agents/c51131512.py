from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    has_coa: bool
    is_compliant: bool

def validate_chemical(state: ProcurementState):
    compliant = state['purity_level'] >= 99.0 and state['has_coa']
    return {'is_compliant': compliant}

def check_procurement(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemical)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()