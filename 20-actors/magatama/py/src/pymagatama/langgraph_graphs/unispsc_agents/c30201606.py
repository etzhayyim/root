from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_compliance(state: KitchenProcurementState):
    errors = []
    if 'f_rating' not in state['spec_data']:
        errors.append('Missing Formaldehyde E0/E1 certification')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(KitchenProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()