from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiamondState(TypedDict):
    spec_data: dict
    is_verified: bool
    compliance_cleared: bool

def validate_certification(state: DiamondState):
    cert = state['spec_data'].get('kimberley_process_certification')
    return {'is_verified': cert is not None}

def check_compliance(state: DiamondState):
    return {'compliance_cleared': state.get('is_verified', False)}

graph = StateGraph(DiamondState)
graph.add_node('cert_validation', validate_certification)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('cert_validation')
graph.add_edge('cert_validation', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
