from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConferencingState(TypedDict):
    license_count: int
    region: str
    compliance_required: bool

def validate_license(state: ConferencingState):
    if state['license_count'] <= 0: raise ValueError('Invalid license count')
    return {'status': 'validated'}

def check_compliance(state: ConferencingState):
    compliance_status = True if state.get('compliance_required') else False
    return {'compliant': compliance_status}

graph = StateGraph(ConferencingState)
graph.add_node('validate', validate_license)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()