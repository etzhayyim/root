from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MailerTubeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: MailerTubeState):
    errors = []
    if state['spec_data'].get('inner_diameter_mm', 0) <= 0:
        errors.append('Invalid diameter')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(MailerTubeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
