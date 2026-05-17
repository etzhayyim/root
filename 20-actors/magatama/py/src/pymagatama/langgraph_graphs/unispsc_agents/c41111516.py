from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeighingState(TypedDict):
    part_specs: dict
    validation_passed: bool
    calibration_required: bool

def validate_specs(state: WeighingState):
    # Business logic for verifying accessory compatibility
    state['validation_passed'] = 'model_id' in state['part_specs']
    return state

def check_calibration(state: WeighingState):
    # Logic for calibration compliance checks
    state['calibration_required'] = state['part_specs'].get('needs_cal', False)
    return state

graph = StateGraph(WeighingState)
graph.add_node('validate', validate_specs)
graph.add_node('calibration', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibration')
graph.add_edge('calibration', END)
graph = graph.compile()