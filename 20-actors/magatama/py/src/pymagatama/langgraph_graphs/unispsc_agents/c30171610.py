from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WindowState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: WindowState):
    errors = []
    if 'width' not in state['specs'] or state['specs']['width'] <= 0:
        errors.append('Invalid width')
    return {'validation_errors': errors}

def check_compliance(state: WindowState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(WindowState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
