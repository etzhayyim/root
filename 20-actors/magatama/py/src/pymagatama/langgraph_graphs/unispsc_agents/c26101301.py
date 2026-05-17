from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirMotorState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_check: str

def validate_specs(state: AirMotorState):
    required = ['operating_pressure_bar', 'power_output_kw']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_export_compliance(state: AirMotorState):
    compliance = 'CLEARED' if state['specs'].get('power_output_kw', 0) < 50 else 'REVIEW_REQUIRED'
    return {'compliance_check': compliance}

graph = StateGraph(AirMotorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()