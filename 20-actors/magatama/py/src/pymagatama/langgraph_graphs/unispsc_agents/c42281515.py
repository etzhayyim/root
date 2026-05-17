from typing import TypedDict
from langgraph.graph import StateGraph, END

class SterilizationState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: SterilizationState):
    log = []
    compliant = True
    if 'ISO 13485' not in state['spec_data'].get('certifications', []):
        log.append('Missing ISO 13485 certification')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def process_workflow(state: SterilizationState):
    print('Initiating sterilization hardware validation')
    return state

graph = StateGraph(SterilizationState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()