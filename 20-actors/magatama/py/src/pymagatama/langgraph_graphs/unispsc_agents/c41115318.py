from typing import TypedDict
from langgraph.graph import StateGraph, END

class ColorimeterState(TypedDict):
    spec_data: dict
    validation_passed: bool
    calibration_status: str

def validate_specs(state:):
    required = ['Wavelength_Range', 'Calibration_Standard_Certificate']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def check_calibration(state:):
    if state.get('calibration_status') == 'valid':
        return {'validation_passed': True}
    return {'validation_passed': False}

graph = StateGraph(ColorimeterState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()