from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_material(state: PipeState):
    grade = state['spec_data'].get('grade')
    is_valid = grade in ['4130', '4140']
    return {'validation_passed': is_valid}

def check_welding_specs(state: PipeState):
    has_wps = 'wps_file' in state['spec_data']
    return {'validation_passed': state['validation_passed'] and has_wps}

graph = StateGraph(PipeState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_wps', check_welding_specs)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_wps')
graph.add_edge('check_wps', END)
app = graph.compile()
