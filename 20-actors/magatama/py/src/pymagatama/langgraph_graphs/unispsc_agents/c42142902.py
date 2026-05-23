from typing import TypedDict
from langgraph.graph import StateGraph, END

class LensState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_lens_specs(state: LensState):
    required = ['refractive_index', 'coating_type']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specs'}

def approval_workflow(state: LensState):
    return {'validated': True}

graph = StateGraph(LensState)
graph.add_node('validate', validate_lens_specs)
graph.add_node('approve', approval_workflow)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
