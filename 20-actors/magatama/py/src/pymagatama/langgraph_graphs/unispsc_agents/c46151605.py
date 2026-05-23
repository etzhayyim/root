from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SecurityState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    calibrated: bool
    approved: bool

def validate_compliance(state: SecurityState):
    state['approved'] = all(['safety_cert' in state['compliance_docs'], state['calibrated']])
    return state

def route_verification(state: SecurityState):
    return 'process' if state['approved'] else END

graph = StateGraph(SecurityState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_verification, {'process': 'process'})
graph.add_edge('process', END)
graph = graph.compile()
