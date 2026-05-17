from typing import TypedDict
from langgraph.graph import StateGraph, END

class GinkgoState(TypedDict):
    spec_data: dict
    approved: bool
    validation_errors: list

def validate_purity(state: GinkgoState):
    errors = []
    if state['spec_data'].get('purity_percentage', 0) < 98:
        errors.append('Purity below 98% threshold')
    return {'validation_errors': errors}

def compliance_check(state: GinkgoState):
    is_compliant = len(state.get('validation_errors', [])) == 0
    return {'approved': is_compliant}

graph = StateGraph(GinkgoState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('compliance_check', compliance_check)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()