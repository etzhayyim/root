from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodPressureState(TypedDict):
    device_specs: dict
    validation_results: dict

def validate_calibration(state: BloodPressureState):
    # Simulate calibration check for aneroid unit
    valid = state['device_specs'].get('accuracy_rating', 0) >= 3
    return {'validation_results': {'is_calibrated': valid}}

def check_compliance(state: BloodPressureState):
    # Check for medical certification
    compliant = 'ISO_13485' in state['device_specs']. get('certs', [])
    return {'validation_results': {'is_compliant': compliant}}

graph = StateGraph(BloodPressureState)
graph.add_node('calibrate', validate_calibration)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('calibrate')
graph.add_edge('calibrate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
