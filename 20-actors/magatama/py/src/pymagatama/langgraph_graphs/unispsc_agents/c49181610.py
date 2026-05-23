from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GuardState(TypedDict):
    spec: dict
    validated: bool
    errors: List[str]

def validate_guard_spec(state: GuardState):
    errors = []
    if 'material' not in state['spec']: errors.append('Missing material')
    if 'size' not in state['spec']: errors.append('Missing size')
    return {'validated': len(errors) == 0, 'errors': errors}

graph = StateGraph(GuardState)
graph.add_node('validate', validate_guard_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
