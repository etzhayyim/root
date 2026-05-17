from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: CastState):
    errors = []
    if 'alloy_grade' not in state['spec_data']:
        errors.append('Missing Alloy Grade')
    return {'validation_errors': errors}

def final_check(state: CastState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(CastState)
graph.add_node('validate', validate_material)
graph.add_node('approval', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()