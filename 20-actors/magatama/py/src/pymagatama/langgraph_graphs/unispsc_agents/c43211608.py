from typing import TypedDict
from langgraph.graph import StateGraph, END

class EncoderState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: EncoderState):
    required = ['codec', 'interface']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: EncoderState):
    risk = 'HIGH' if state['specs'].get('encryption') == 'aes-256' else 'LOW'
    return {'compliance_risk': risk}

graph = StateGraph(EncoderState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
