from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LockoutState(TypedDict):
    device_type: str
    compliance_certs: List[str]
    is_approved: bool

def validate_compliance(state: LockoutState):
    required = ['OSHA', 'ANSI']
    all_present = all(cert in state['compliance_certs'] for cert in required)
    return {'is_approved': all_present}

def route_verification(state: LockoutState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(LockoutState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_verification, {'approved': END, 'rejected': END})
graph.compile()
