from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_materials(state: PipeState):
    grade = state['spec_data'].get('grade')
    validated = grade is not None
    return {'validation_passed': validated}

def process_assembly(state: PipeState):
    return {'validation_passed': True}

graph = StateGraph(PipeState)
graph.add_node('validation', validate_materials)
graph.add_node('assembly', process_assembly)
graph.set_entry_point('validation')
graph.add_edge('validation', 'assembly')
graph.add_edge('assembly', END)
graph = graph.compile()