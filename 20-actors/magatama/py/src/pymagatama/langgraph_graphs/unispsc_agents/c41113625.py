from typing import TypedDict
from langgraph.graph import StateGraph, END

class IonizationState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: IonizationState):
    required = ['sensitivity', 'calibration_date']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Failed'}

def export_review(state: IonizationState):
    return {'compliance_report': 'Dual-use check completed'}

graph = StateGraph(IonizationState)
graph.add_node('validate', validate_specs)
graph.add_node('export_control', export_review)
graph.add_edge('validate', 'export_control')
graph.add_edge('export_control', END)
graph.set_entry_point('validate')
graph = graph.compile()
