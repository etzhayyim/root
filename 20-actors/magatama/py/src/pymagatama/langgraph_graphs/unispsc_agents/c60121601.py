from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MannequinState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: MannequinState):
    errors = []
    if state['specs'].get('height', 0) < 100:
        errors.append('Height below minimum for retail display')
    return {'validation_errors': errors}

def approval_step(state: MannequinState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(MannequinState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()