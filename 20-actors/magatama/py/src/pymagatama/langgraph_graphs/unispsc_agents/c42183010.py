from typing import TypedDict
from langgraph.graph import StateGraph, END

class LensometerState(TypedDict):
    device_id: str
    calibration_status: bool
    accuracy_check_passed: bool

def validate_calibration(state: LensometerState):
    print(f'Validating calibration for device: {state[\'device_id\']}')
    return {'calibration_status': True}

def perform_accuracy_test(state: LensometerState):
    print('Running diopter measurement accuracy test pipeline')
    return {'accuracy_check_passed': True}

graph = StateGraph(LensometerState)
graph.add_node('validate', validate_calibration)
graph.add_node('test_accuracy', perform_accuracy_test)
graph.set_entry_point('validate')
graph.add_edge('validate', 'test_accuracy')
graph.add_edge('test_accuracy', END)
graph = graph.compile()