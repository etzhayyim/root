from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    quality_docs: list
    is_validated: bool

def validate_gmp_cert(state: ProcurementState):
    state['is_validated'] = 'GMP' in str(state['quality_docs'])
    return state

def check_compliance(state: ProcurementState):
    return 'compliance_passed' if state['is_validated'] else 'compliance_failed'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gmp_cert)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
