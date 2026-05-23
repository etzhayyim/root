from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TwistTieState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_materials(state: TwistTieState):
    errors = []
    if state['spec_data'].get('wire_gauge', 0) < 0.2:
        errors.append('Wire gauge below safety minimum')
    return {'validation_errors': errors}

def approval_check(state: TwistTieState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(TwistTieState)
graph.add_node('validate', validate_materials)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
