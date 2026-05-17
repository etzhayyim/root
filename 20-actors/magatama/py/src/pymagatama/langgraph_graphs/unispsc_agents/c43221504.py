from typing import TypedDict
from langgraph.graph import StateGraph, END

class PBXState(TypedDict):
    requirements: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: PBXState):
    # Simulate CAD/Spec validation for PBX hardware
    required_keys = ['extension_count', 'sip_standard']
    state['validation_passed'] = all(k in state['requirements'] for k in required_keys)
    return state

def check_compliance(state: PBXState):
    # Logic for regulatory export controls
    state['compliance_risk'] = 'Medium' if state.get('validation_passed') else 'High'
    return state

graph = StateGraph(PBXState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()