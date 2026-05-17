from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PumpState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: PumpState):
    errors = []
    if state['specs'].get('flow_rate', 0) <= 0:
        errors.append('Invalid flow rate')
    return {'validation_errors': errors}

def approval_check(state: PumpState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()