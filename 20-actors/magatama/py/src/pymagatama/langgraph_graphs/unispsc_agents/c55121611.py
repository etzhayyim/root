from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TapeSpecState(TypedDict):
    spec: dict
    validated: bool
    errors: List[str]

def validate_specs(state: TapeSpecState):
    errors = []
    if 'width' not in state['spec']: errors.append('Width missing')
    if 'material' not in state['spec']: errors.append('Material missing')
    return {'validated': len(errors) == 0, 'errors': errors}

def route_by_validation(state: TapeSpecState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(TapeSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
