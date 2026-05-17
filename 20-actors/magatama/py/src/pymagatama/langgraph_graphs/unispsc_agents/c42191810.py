from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MattressState(TypedDict):
    spec_data: dict
    compliant: bool
    validation_errors: List[str]

def validate_medical_standards(state: MattressState):
    errors = []
    if not state['spec_data'].get('iso_13485'):
        errors.append('Missing ISO 13485 certification')
    return {'compliant': len(errors) == 0, 'validation_errors': errors}

def process_procurement(state: MattressState):
    print('Processing procurement for patient care mattress...')
    return state

graph = StateGraph(MattressState)
graph.add_node('validate', validate_medical_standards)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

graph = graph.compile()