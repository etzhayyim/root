from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalSpecState(TypedDict):
    spec_content: dict
    validation_passed: bool
    error_logs: list

def validate_surgical_specs(state: SurgicalSpecState):
    specs = state['spec_content']
    errors = []
    if 'iso_13485_certification' not in specs:
        errors.append('Missing ISO 13485 certification.')
    return {'validation_passed': len(errors) == 0, 'error_logs': errors}

def prepare_logistics(state: SurgicalSpecState):
    return {'error_logs': state['error_logs'] + ['Logistics routing initialized for sterile medical device.']}

graph_builder = StateGraph(SurgicalSpecState)
graph_builder.add_node('validate', validate_surgical_specs)
graph_builder.add_node('logistics', prepare_logistics)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'logistics')
graph_builder.add_edge('logistics', END)
graph = graph_builder.compile()
