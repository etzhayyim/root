from langgraph.graph import StateGraph, END
from typing import TypedDict
class RecorderState(TypedDict):
    spec_data: dict
    validation_passed: bool
def validate_specs(state: RecorderState):
    required = ['accuracy', 'sampling_rate']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}
def check_calibration(state: RecorderState):
    return {'validation_passed': state.get('spec_data', {}).get('calibration_valid', False)}
graph = StateGraph(RecorderState)
graph.add_node('validate', validate_specs)
graph.add_node('calibration', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibration')
graph.add_edge('calibration', END)
graph = graph.compile()
