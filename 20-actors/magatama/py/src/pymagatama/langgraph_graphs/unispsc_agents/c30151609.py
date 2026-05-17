from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RoofCurbState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_structural_specs(state: RoofCurbState):
    errors = []
    if not state['specs'].get('load_capacity'):
        errors.append('Missing load capacity requirement')
    return {'validation_errors': errors}

def safety_check(state: RoofCurbState):
    is_safe = len(state['validation_errors']) == 0
    return {'is_approved': is_safe}

graph = StateGraph(RoofCurbState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()