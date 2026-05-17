from typing import TypedDict
from langgraph.graph import StateGraph, END

class InterferometerState(TypedDict):
    specs: dict
    validation_passed: bool
    export_control_check: bool

def validate_specs(state: InterferometerState):
    # Business logic for interferometer procurement specs
    required_keys = ['accuracy_nm', 'laser_class']
    passed = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': passed}

def check_export_controls(state: InterferometerState):
    # Dual-use regulatory check automation
    is_controlled = state['specs'].get('accuracy_nm', 1000) < 10
    return {'export_control_check': not is_controlled}

graph = StateGraph(InterferometerState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()