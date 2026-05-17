from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: ProcessingState):
    log = []
    compliant = True
    if 'frequency_range_ghz' not in state['spec_data']:
        log.append('Missing frequency range')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def export_control_check(state: ProcessingState):
    # Mock logic for dual-use export control screening
    return {'validation_log': state['validation_log'] + ['Export control check passed']}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()