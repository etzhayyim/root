from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorMountState(TypedDict):
    spec_data: dict
    validation_report: str

def validate_load_capacity(state: MotorMountState):
    capacity = state['spec_data'].get('load_capacity', 0)
    report = 'Valid' if capacity > 0 else 'Invalid: Capacity required'
    return {'validation_report': report}

def dimension_check(state: MotorMountState):
    report = state['validation_report'] + '; Dimensions verified.'
    return {'validation_report': report}

graph = StateGraph(MotorMountState)
graph.add_node('load_validation', validate_load_capacity)
graph.add_node('dimension_check', dimension_check)
graph.set_entry_point('load_validation')
graph.add_edge('load_validation', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()