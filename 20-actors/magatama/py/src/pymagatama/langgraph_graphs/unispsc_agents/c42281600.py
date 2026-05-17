from typing import TypedDict
from langgraph.graph import StateGraph, END

class SterilizationState(TypedDict):
    product_id: str
    compliance_docs: list
    is_approved: bool

def validate_safety_data(state: SterilizationState):
    # Simulate SDS validation logic
    state['is_approved'] = True
    return state

def check_compliance(state: SterilizationState):
    # Check for regulatory certifications
    return {'is_approved': len(state['compliance_docs']) > 0}

graph = StateGraph(SterilizationState)
graph.add_node('validate_sds', validate_safety_data)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('validate_sds', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('validate_sds')
graph = graph.compile()