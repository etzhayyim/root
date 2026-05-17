from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RamPumpState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: RamPumpState):
    errors = []
    if state['spec_data'].get('head', 0) <= 0:
        errors.append('Invalid pumping head')
    return {'validation_errors': errors}

def approval_check(state: RamPumpState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(RamPumpState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()