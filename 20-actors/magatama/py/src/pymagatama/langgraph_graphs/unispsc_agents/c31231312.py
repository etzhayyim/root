from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CementSpecState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: CementSpecState):
    errors = []
    if state['specs'].get('wall_thickness', 0) < 10:
        errors.append('Wall thickness below safety threshold')
    return {'validation_errors': errors}

def approval_step(state: CementSpecState):
    is_ok = len(state['validation_errors']) == 0
    return {'is_approved': is_ok}

graph = StateGraph(CementSpecState)
graph.add_node('validate', validate_dimensions)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
