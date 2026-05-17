from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabelingState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: LabelingState):
    errors = []
    if state['spec_sheet'].get('speed', 0) <= 0:
        errors.append('Invalid labeling speed')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LabelingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()