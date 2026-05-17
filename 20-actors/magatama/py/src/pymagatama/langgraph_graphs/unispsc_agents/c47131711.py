from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: DispenserState):
    errors = []
    if 'flow_rate' not in state['specs']: errors.append('Missing flow rate')
    return {'validation_errors': errors}

def approval_check(state: DispenserState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
app = graph.compile()