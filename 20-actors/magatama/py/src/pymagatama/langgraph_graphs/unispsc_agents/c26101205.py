from typing import TypedDict
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: ServoState):
    errors = []
    if state['spec_data'].get('encoder_resolution', 0) < 1000:
        errors.append('Insufficient encoder resolution')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def approval_step(state: ServoState):
    return {'is_approved': state['is_approved']}

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
app = graph.compile()
