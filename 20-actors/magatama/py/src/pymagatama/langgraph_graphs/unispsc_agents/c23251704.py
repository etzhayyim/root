from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: ForgingState):
    errors = []
    if 'force_kn' not in state['specifications']: errors.append('Missing force intensity')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
