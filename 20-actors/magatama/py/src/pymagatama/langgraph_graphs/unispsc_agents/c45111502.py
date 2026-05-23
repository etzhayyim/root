from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LecternState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: LecternState):
    errors = []
    if state['specs'].get('weight_kg', 0) > 20: errors.append('Weight exceeds desktop load limit.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(LecternState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
compile = graph.compile()
