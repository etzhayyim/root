from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CuvetteState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: CuvetteState):
    errors = []
    if 'gap' not in state['spec_data'] or state['spec_data']['gap'] <= 0:
        errors.append('Invalid electrode gap.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def approval_step(state: CuvetteState):
    return {'is_approved': state['is_approved']}

graph = StateGraph(CuvetteState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
