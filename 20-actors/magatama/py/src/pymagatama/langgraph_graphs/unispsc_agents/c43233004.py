from typing import TypedDict
from langgraph.graph import StateGraph, END

class OSProcurementState(TypedDict):
    license_sku: str
    compliance_status: bool
    is_approved: bool

def validate_compliance(state: OSProcurementState):
    # Simulate validation logic for OS deployment
    state['compliance_status'] = 'security_patch' in state['license_sku']
    return {'compliance_status': state['compliance_status']}

def approval_step(state: OSProcurementState):
    return {'is_approved': state['compliance_status']}

graph = StateGraph(OSProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
app = graph.compile()