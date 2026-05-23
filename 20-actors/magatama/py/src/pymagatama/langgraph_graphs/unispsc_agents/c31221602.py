from typing import TypedDict
from langgraph.graph import StateGraph, END

class TanningState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_tanning_spec(state: TanningState):
    errors = []
    if state['spec_data'].get('tannin_content_percentage', 0) < 50:
        errors.append('Insufficient tannin concentration')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(TanningState)
graph.add_node('validate', validate_tanning_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
