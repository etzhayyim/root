from typing import TypedDict
from langgraph.graph import StateGraph, END

class IceMakerState(TypedDict):
    specs: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: IceMakerState):
    errors = []
    if state['specs'].get('production_rate', 0) <= 0:
        errors.append('Invalid production rate')
    return {'validation_errors': errors}

def approval_step(state: IceMakerState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(IceMakerState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
