from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    part_data: dict
    validation_passed: bool
    error_log: list

def validate_material(state: ProcessingState):
    # Mock validation for Inconel specs
    is_valid = state['part_data'].get('material') == 'Inconel'
    return {'validation_passed': is_valid}

def check_welds(state: ProcessingState):
    # Specialized check for sonic weld integrity
    passed = state['part_data'].get('welding_certification') is not None
    return {'validation_passed': state['validation_passed'] and passed}

graph = StateGraph(ProcessingState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_welds', check_welds)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_welds')
graph.add_edge('check_welds', END)
graph = graph.compile()