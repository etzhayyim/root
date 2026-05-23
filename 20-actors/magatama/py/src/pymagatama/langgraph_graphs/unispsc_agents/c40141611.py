from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_valve_specs(state: ValveProcurementState):
    required = ['pressure_rating', 'material']
    passed = all(k in state['spec_data'] for k in required)
    return {**state, 'validation_passed': passed}

def generate_compliance(state: ValveProcurementState):
    report = 'Compliance confirmed for high-pressure industrial application.' if state['validation_passed'] else 'Compliance failed.'
    return {**state, 'compliance_report': report}

graph = StateGraph(ValveProcurementState)
graph.add_node('validate', validate_valve_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
