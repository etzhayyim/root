from typing import TypedDict
from langgraph.graph import StateGraph, END

class AdapterState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_tech_specs(state: AdapterState):
    errors = []
    if 'impedance' not in state['spec_data']:
        errors.append('Impedance must be specified for PBX matching')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def process_adapter_workflow(state: AdapterState):
    return {'is_approved': True}

graph = StateGraph(AdapterState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('process', process_adapter_workflow)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()