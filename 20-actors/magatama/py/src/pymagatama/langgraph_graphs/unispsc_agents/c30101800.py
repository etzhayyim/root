from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChannelState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: ChannelState):
    dims = state['spec_data'].get('dimensions', {})
    if dims.get('thickness', 0) <= 0:
        state['validation_errors'].append('Invalid thickness value')
    return {'is_approved': len(state['validation_errors']) == 0}

def process_material_cert(state: ChannelState):
    cert = state['spec_data'].get('cert_type')
    if not cert:
        state['validation_errors'].append('Missing material certification')
    return state

graph = StateGraph(ChannelState)
graph.add_node('validate', validate_dimensions)
graph.add_node('certify', process_material_cert)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()