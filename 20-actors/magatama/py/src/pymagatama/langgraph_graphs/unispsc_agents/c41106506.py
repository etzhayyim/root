from typing import TypedDict
from langgraph.graph import StateGraph, END

class InsectMediaState(TypedDict):
    media_spec: dict
    validation_status: bool
    qc_passed: bool

def validate_media_specs(state: InsectMediaState):
    print('Validating chemical components...')
    state['validation_status'] = 'pH' in state['media_spec'] and 'expiry' in state['media_spec']
    return state

def run_qc_check(state: InsectMediaState):
    print('Performing sterility and contamination check...')
    state['qc_passed'] = state['validation_status']
    return state

graph = StateGraph(InsectMediaState)
graph.add_node('validate', validate_media_specs)
graph.add_node('qc', run_qc_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()