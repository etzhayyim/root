from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    compliance_status: bool
    regulatory_approval: bool

def validate_license(state: ProcurementState):
    state['compliance_status'] = True
    return 'validate_license'

def check_regulatory_approval(state: ProcurementState):
    state['regulatory_approval'] = True
    return 'check_regulatory_approval'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_license)
graph.add_node('approve', check_regulatory_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
