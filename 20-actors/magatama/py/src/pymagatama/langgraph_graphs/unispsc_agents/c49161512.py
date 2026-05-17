from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LacrosseSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: LacrosseSpecState):
    errors = []
    if not (140 <= state['spec_data'].get('weight', 0) <= 149):
        errors.append('Weight must be between 140g and 149g')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LacrosseSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()