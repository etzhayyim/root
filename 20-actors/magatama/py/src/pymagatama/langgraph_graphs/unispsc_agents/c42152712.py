from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrthoState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_biocompatibility(state: OrthoState):
    state['validation_passed'] = 'ISO_10993' in state['spec_data'].get('certs', [])
    return state

def check_dimensions(state: OrthoState):
    if state['validation_passed']:
        print('Checking dimensions against molar sizing standards...')
    return state

graph = StateGraph(OrthoState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()
