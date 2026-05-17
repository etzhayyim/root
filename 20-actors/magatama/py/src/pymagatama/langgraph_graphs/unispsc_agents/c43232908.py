from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SoftwareProcurementState(TypedDict):
    software_version: str
    compliance_cleared: bool
    steps: List[str]

def validate_compliance(state: SoftwareProcurementState):
    # Simulate export control check
    state['compliance_cleared'] = True
    state['steps'].append('Compliance Verified')
    return state

def provision_license(state: SoftwareProcurementState):
    state['steps'].append('License Key Generated')
    return state

graph = StateGraph(SoftwareProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('provision', provision_license)
graph.set_entry_point('validate')
graph.add_edge('validate', 'provision')
graph.add_edge('provision', END)
app = graph.compile()