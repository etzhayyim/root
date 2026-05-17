from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnchorProcurementState(TypedDict):
    spec_requirements: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: AnchorProcurementState):
    errors = []
    if state['spec_requirements'].get('load_capacity', 0) <= 0:
        errors.append('Invalid load capacity')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(AnchorProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()