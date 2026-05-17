from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HeadgearState(TypedDict):
    material_specs: dict
    compliance_certs: List[str]
    safety_rating: float
    status: str

def validate_compliance(state: HeadgearState) -> HeadgearState:
    if 'ASTM' not in state['compliance_certs']:
        state['status'] = 'REJECTED_COMPLIANCE'
    return state

def inspect_spec(state: HeadgearState) -> HeadgearState:
    if state['safety_rating'] < 8.0:
        state['status'] = 'FAILED_SAFETY_THRESHOLD'
    else:
        state['status'] = 'PASSED_QA'
    return state

graph = StateGraph(HeadgearState)
graph.add_node('validate', validate_compliance)
graph.add_node('inspect', inspect_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()