from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PumpState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_status: List[str]

def validate_specs(state: PumpState):
    required = ['flow_accuracy', 'iso_compliance']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: PumpState):
    errors = []
    if state['specs'].get('flow_accuracy', 0) > 0.05:
        errors.append('Flow accuracy outside tolerance')
    return {'compliance_status': errors}

graph = StateGraph(PumpState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()