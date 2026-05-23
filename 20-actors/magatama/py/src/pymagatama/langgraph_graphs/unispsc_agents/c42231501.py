from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    device_id: str
    spec_compliance: bool
    calibration_status: str

def validate_spec(state: PumpState) -> PumpState:
    print(f'Validating specs for {state['device_id']}')
    state['spec_compliance'] = True
    return state

def check_calibration(state: PumpState) -> PumpState:
    print(f'Checking calibration for {state['device_id']}')
    state['calibration_status'] = 'VERIFIED'
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_spec)
graph.add_node('calibrate', check_calibration)
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph.set_entry_point('validate')
graph = graph.compile()
