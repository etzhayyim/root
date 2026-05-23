from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ArmbandState(TypedDict):
    spec_details: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ArmbandState):
    errors = []
    if not state['spec_details'].get('material'):
        errors.append('Missing material specification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approval_step(state: ArmbandState):
    print('Proceeding to procurement approval for armbands')
    return {'is_compliant': True}

graph = StateGraph(ArmbandState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
