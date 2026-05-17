from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RudderState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_specs(state: RudderState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material grade')
    if 'certification' not in state['specs']: errors.append('Missing classification certificate')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_verification(state: RudderState):
    return 'validate' if not state['approved'] else END

graph = StateGraph(RudderState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()