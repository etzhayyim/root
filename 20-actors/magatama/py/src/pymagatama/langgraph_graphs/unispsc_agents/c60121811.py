from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InkState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_chemistry(state: InkState):
    errors = []
    if state['spec_data'].get('flash_point', 100) < 23:
        errors.append('High flammability risk classified as dangerous good')
    return {'validation_errors': errors}

def approval_node(state: InkState):
    approved = len(state['validation_errors']) == 0
    return {'approved': approved}

graph = StateGraph(InkState)
graph.add_node('validate', validate_chemistry)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()