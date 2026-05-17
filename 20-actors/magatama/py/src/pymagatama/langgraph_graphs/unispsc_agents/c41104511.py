from typing import TypedDict
from langgraph.graph import StateGraph, END
class HybridState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
def validate_specs(state: HybridState):
    required = ['temp_accuracy', 'rot_speed']
    passed = all(k in state['spec_sheet'] for k in required)
    return {'validation_passed': passed}
def check_calibration(state: HybridState):
    if state.get('validation_passed'):
        print('Proceeding to calibration check.')
    return 'calibration_verified'
graph = StateGraph(HybridState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', check_calibration)
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph.set_entry_point('validate')
app = graph.compile()