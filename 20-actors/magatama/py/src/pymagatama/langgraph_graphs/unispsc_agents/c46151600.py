from typing import TypedDict
from langgraph.graph import StateGraph, END

class SecurityState(TypedDict):
    equipment_id: str
    compliance_checked: bool
    security_clearance: bool

def validate_compliance(state: SecurityState):
    state['compliance_checked'] = True
    return 'checked'

def verify_clearance(state: SecurityState):
    state['security_clearance'] = True
    return 'verified'

graph = StateGraph(SecurityState)
graph.add_node('compliance', validate_compliance)
graph.add_node('security', verify_clearance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'security')
graph.add_edge('security', END)
compile = graph.compile()
