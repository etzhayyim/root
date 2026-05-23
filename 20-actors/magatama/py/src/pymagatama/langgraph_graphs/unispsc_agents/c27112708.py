from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SanderState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_specs(state: SanderState):
    errors = []
    if state['specs'].get('voltage') not in [110, 220, 240]:
        errors.append('Invalid voltage specification.')
    if not state['specs'].get('dust_extraction'):
        errors.append('Missing required dust extraction feature.')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(SanderState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
