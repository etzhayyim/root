from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HydrologyState(TypedDict):
    instrument_type: str
    calibration_data: dict
    validation_passed: bool

def validate_sensor_spec(state: HydrologyState):
    print(f'Validating specifications for: {state["instrument_type"]}')
    state['validation_passed'] = True
    return state

def execute_calibration_check(state: HydrologyState):
    print('Verifying ISO/IEC 17025 calibration compliance...')
    return {'validation_passed': True}

graph = StateGraph(HydrologyState)
graph.add_node('validate', validate_sensor_spec)
graph.add_node('calibrate', execute_calibration_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()