from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class InjectionState(TypedDict):
    device_id: str
    calibration_data: dict
    validation_passed: bool
    error_log: list

def validate_device(state: InjectionState) -> InjectionState:
    # Logic to verify sensor calibration and sterility status
    state['validation_passed'] = all(k in state['calibration_data'] for k in ['sensor_drift', 'sterile_seal'])
    return state

def execute_qc(state: InjectionState) -> InjectionState:
    if not state['validation_passed']:
        state['error_log'].append('Calibration check failed')
    return state

graph = StateGraph(InjectionState)
graph.add_node('validate', validate_device)
graph.add_node('qc', execute_qc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()
