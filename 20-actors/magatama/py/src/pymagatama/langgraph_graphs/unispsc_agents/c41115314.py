from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PolarimeterState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: PolarimeterState):
    errors = []
    if state['specifications'].get('accuracy', 0) < 0.001:
        errors.append('Accuracy below laboratory threshold')
    return {'validation_errors': errors}

def approval_step(state: PolarimeterState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(PolarimeterState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
