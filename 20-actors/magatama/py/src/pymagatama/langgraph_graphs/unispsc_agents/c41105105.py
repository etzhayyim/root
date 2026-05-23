from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: PumpState):
    required = ['flow_rate', 'pressure', 'material']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: PumpState):
    if 'hazardous' in state['specs'].get('application', ''):
        return {'compliance_risk': 'high'}
    return {'compliance_risk': 'low'}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
