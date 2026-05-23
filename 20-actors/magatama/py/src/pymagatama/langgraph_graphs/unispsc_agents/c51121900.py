from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaSpec(TypedDict):
    drug_name: str
    gmp_certified: bool
    compliance_check: bool

def validate_compliance(state: PharmaSpec):
    state['compliance_check'] = state['gmp_certified']
    return state

def route_procurement(state: PharmaSpec):
    return 'APPROVED' if state['compliance_check'] else 'REJECTED'

graph = StateGraph(PharmaSpec)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
