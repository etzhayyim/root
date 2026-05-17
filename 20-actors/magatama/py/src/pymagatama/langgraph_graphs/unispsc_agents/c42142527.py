from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningWireState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_dimensions(state: CleaningWireState):
    diameter = state['spec_data'].get('diameter')
    is_valid = 0.1 <= diameter <= 2.0
    return {'validation_results': [f'Dimension valid: {is_valid}']}

def check_compliance(state: CleaningWireState):
    cert = state['spec_data'].get('cert')
    return {'is_approved': cert == 'ISO-13485'}

graph = StateGraph(CleaningWireState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()