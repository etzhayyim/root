from typing import TypedDict
from langgraph.graph import StateGraph, END

class FrictionState(TypedDict):
    spec_data: dict
    validation_passed: bool
    calibration_status: str

def validate_specs(state: FrictionState):
    # Simulate CAD and component validation logic
    state['validation_passed'] = all(k in state['spec_data'] for k in ['material', 'precision'])
    print(f'Validation result: {state['validation_passed']}')
    return {'validation_passed': state['validation_passed']}

def verify_calibration(state: FrictionState):
    state['calibration_status'] = 'CERTIFIED' if state.get('validation_passed') else 'PENDING'
    return {'calibration_status': state['calibration_status']}

graph = StateGraph(FrictionState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', verify_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()