from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class WorkflowState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_luminance_spec(state: WorkflowState):
    luminance = state['spec_data'].get('luminance_nit', 0)
    if luminance < 3000:
        state['validation_errors'].append('Insufficient luminance for diagnostic viewing')
    return state

def check_certification(state: WorkflowState):
    if not state['spec_data'].get('medical_device_certification'):
        state['validation_errors'].append('Missing required medical device certification')
    return state

def compile_and_finalize(state: WorkflowState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(WorkflowState)
graph.add_node('validate_light', validate_luminance_spec)
graph.add_node('check_cert', check_certification)
graph.add_node('finalize', compile_and_finalize)
graph.set_entry_point('validate_light')
graph.add_edge('validate_light', 'check_cert')
graph.add_edge('check_cert', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
