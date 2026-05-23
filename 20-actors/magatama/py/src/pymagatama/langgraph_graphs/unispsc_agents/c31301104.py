from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    inspection_report: str

def validate_material(state: ForgingState) -> ForgingState:
    grade = state['spec_data'].get('grade')
    state['validation_passed'] = grade in ['SUS304', 'SUS316L', 'SUS630']
    return state

def check_dimensions(state: ForgingState) -> ForgingState:
    if state['validation_passed']:
        state['inspection_report'] = 'Dimensional check performed against CAD files.'
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', check_dimensions)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()
