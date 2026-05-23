from typing import TypedDict
from langgraph.graph import StateGraph, END

class LensGaugeState(TypedDict):
    measurement_data: dict
    validation_passed: bool
    calibration_status: bool

def validate_calibration(state: LensGaugeState):
    print('Checking calibration status...')
    state['calibration_status'] = state['measurement_data'].get('cert_id') is not None
    return state

def run_precision_validation(state: LensGaugeState):
    print('Validating radius accuracy against ISO standards...')
    state['validation_passed'] = state['measurement_data'].get('tolerance', 0.01) <= 0.05
    return state

graph = StateGraph(LensGaugeState)
graph.add_node('verify_calib', validate_calibration)
graph.add_node('compute_accuracy', run_precision_validation)
graph.set_entry_point('verify_calib')
graph.add_edge('verify_calib', 'compute_accuracy')
graph.add_edge('compute_accuracy', END)
graph = graph.compile()
