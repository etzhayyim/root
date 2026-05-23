from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolingState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_tooling_specs(state: ToolingState):
    required = ['material_grade', 'bending_angle_tolerance']
    valid = all(key in state['spec_data'] for key in required)
    return {'validation_result': valid}

graph = StateGraph(ToolingState)
graph.add_node('validate', validate_tooling_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
