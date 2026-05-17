from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MattressState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: MattressState):
    errors = []
    if 'pressure_redistribution_index' not in state['spec_data']:
        errors.append('Missing pressure redistribution metric')
    return {'validation_errors': errors}

def approval_check(state: MattressState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(MattressState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()