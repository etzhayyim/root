from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ZincState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: ZincState):
    errors = []
    if state['part_specs'].get('thickness', 0) < 0.5:
        errors.append('Plate thickness below structural minimum.')
    return {'validation_errors': errors}

def check_compliance(state: ZincState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(ZincState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()