from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    license_valid: bool
    compliance_check: bool
    items: List[str]

def validate_license(state: ProcurementState):
    state['license_valid'] = True
    return 'compliance'

def check_compliance(state: ProcurementState):
    state['compliance_check'] = True
    return 'end'

graph = StateGraph(ProcurementState)
graph.add_node('verify', validate_license)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('verify')
graph.add_edge('verify', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()