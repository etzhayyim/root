from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MicroscopeState(TypedDict):
    model_id: str
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: MicroscopeState):
    errors = []
    if state['specs'].get('magnification', 0) < 40:
        errors.append('Magnification below research standard.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: MicroscopeState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(MicroscopeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()