from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotionControlState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: MotionControlState):
    required = ['Axis Count', 'Communication Protocol']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: MotionControlState):
    risk = 'High' if state['specs'].get('Safety Certification Level') == 'SIL3' else 'Low'
    return {'compliance_risk': risk}

graph = StateGraph(MotionControlState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

graph = graph.compile()
