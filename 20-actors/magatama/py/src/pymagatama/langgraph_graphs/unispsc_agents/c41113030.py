from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScannerState(TypedDict):
    device_id: str
    radiological_check: bool
    calibration_status: bool
    final_approval: bool

def validate_radiological_safety(state: ScannerState):
    print(f'Validating safety compliance for {state[\'device_id\']}')
    return {'radiological_check': True}

def perform_calibration_check(state: ScannerState):
    print('Verifying detector calibration logs...')
    return {'calibration_status': True}

graph = StateGraph(ScannerState)
graph.add_node('safety_check', validate_radiological_safety)
graph.add_node('calibration', perform_calibration_check)
graph.add_edge('safety_check', 'calibration')
graph.add_edge('calibration', END)
graph.set_entry_point('safety_check')
graph = graph.compile()