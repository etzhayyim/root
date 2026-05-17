from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    specs: dict
    validation_result: bool
    errors: List[str]

def validate_pipe_specs(state: PipeState):
    errors = []
    if not state['specs'].get('material'):
        errors.append('Missing material type')
    if state['specs'].get('pressure', 0) <= 0:
        errors.append('Invalid pressure rating')
    return {'validation_result': len(errors) == 0, 'errors': errors}

def route_by_validation(state: PipeState):
    return 'validate' if not state['validation_result'] else END

graph = StateGraph(PipeState)
graph.add_node('validate', validate_pipe_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()