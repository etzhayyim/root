from typing import TypedDict
from langgraph.graph import StateGraph, END

class GeneratorEnclosureState(TypedDict):
    spec_data: dict
    compliance_score: float
    validation_errors: list

def validate_acoustic_specs(state: GeneratorEnclosureState) -> GeneratorEnclosureState:
    if state['spec_data'].get('db_reduction', 0) < 30:
        state['validation_errors'].append('Insufficient noise reduction rating')
    return state

def check_fire_rating(state: GeneratorEnclosureState) -> GeneratorEnclosureState:
    if not state['spec_data'].get('fire_cert'):
        state['validation_errors'].append('Missing fire safety certification')
    return state

graph = StateGraph(GeneratorEnclosureState)
graph.add_node('validate_acoustic', validate_acoustic_specs)
graph.add_node('check_fire', check_fire_rating)
graph.set_entry_point('validate_acoustic')
graph.add_edge('validate_acoustic', 'check_fire')
graph.add_edge('check_fire', END)
graph = graph.compile()
