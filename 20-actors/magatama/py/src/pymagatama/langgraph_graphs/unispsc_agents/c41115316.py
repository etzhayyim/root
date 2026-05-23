from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReflectometerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: ReflectometerState):
    required = ['Wavelength_Range', 'Dynamic_Range']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def calibrate_workflow(state: ReflectometerState):
    if state.get('validation_passed'):
        print('Proceeding to calibration check...')
    return state

graph = StateGraph(ReflectometerState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', calibrate_workflow)
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph.set_entry_point('validate')
app = graph.compile()
