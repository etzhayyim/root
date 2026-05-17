from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoldProcessingState(TypedDict):
    material_specs: dict
    validation_passed: bool
    error_log: list

def validate_material(state: MoldProcessingState):
    grade = state['material_specs'].get('grade')
    return {'validation_passed': grade is not None}

def check_dimensions(state: MoldProcessingState):
    return {'validation_passed': True}

graph = StateGraph(MoldProcessingState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
app = graph.compile()