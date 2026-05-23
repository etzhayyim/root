from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SeamGaugeState(TypedDict):
    data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: SeamGaugeState):
    errors = []
    if state['data'].get('accuracy', 0) > 0.05:
        errors.append('Accuracy exceeds tolerance threshold of 0.05mm')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def approval_step(state: SeamGaugeState):
    print(f'Approval status: {state['is_approved']}')
    return state

graph = StateGraph(SeamGaugeState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
