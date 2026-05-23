from langgraph.graph import StateGraph, END
from typing import TypedDict

class PelletizerState(TypedDict):
    specs: dict
    validation_errors: list
    is_approved: bool

def validate_throughput(state: PelletizerState):
    errors = []
    if state['specs'].get('throughput_capacity_tph', 0) <= 0:
        errors.append('Invalid throughput capacity')
    return {'validation_errors': errors}

def approval_node(state: PelletizerState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(PelletizerState)
graph.add_node('validate', validate_throughput)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
