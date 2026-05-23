from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnchorProcureState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: AnchorProcureState):
    errors = []
    if not state['specifications'].get('tensile_strength'):
        errors.append('Missing tensile strength')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(AnchorProcureState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
