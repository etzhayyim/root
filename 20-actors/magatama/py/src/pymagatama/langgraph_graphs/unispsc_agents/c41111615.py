from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserMeasureState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: LaserMeasureState):
    required = ['laser_class_rating', 'measurement_accuracy_mm']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def perform_compliance_check(state: LaserMeasureState):
    if state['validation_passed']:
        return {'compliance_report': 'Validated against ISO standards'}
    return {'compliance_report': 'Missing mandatory technical specifications'}

graph = StateGraph(LaserMeasureState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', perform_compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()