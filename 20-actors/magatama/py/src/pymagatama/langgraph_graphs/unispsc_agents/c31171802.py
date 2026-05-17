from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImpellerState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_risk: bool

def validate_specs(state: ImpellerState):
    required = ['material', 'tolerance', 'balance']
    valid = all(key in state['spec_data'] for key in required)
    return {'validation_status': valid}

def check_compliance(state: ImpellerState):
    risk = state['spec_data'].get('material') == 'restricted_alloy'
    return {'compliance_risk': risk}

graph = StateGraph(ImpellerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()