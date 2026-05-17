from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperState(TypedDict):
    spec_sheet: dict
    validation_passed: bool

def validate_materials(state: CopperState):
    grade = state['spec_sheet'].get('grade')
    return {'validation_passed': grade is not None}

def process_dimensions(state: CopperState):
    return {'validation_passed': True}

graph = StateGraph(CopperState)
graph.add_node('validate', validate_materials)
graph.add_node('dimensions', process_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
app = graph.compile()