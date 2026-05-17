from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_control_check: bool

def validate_specs(state: CameraState):
    required = ['sensor', 'format']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def check_export_compliance(state: CameraState):
    is_controlled = state['spec_data'].get('high_speed_capture', False)
    return {'export_control_check': not is_controlled}

graph = StateGraph(CameraState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()