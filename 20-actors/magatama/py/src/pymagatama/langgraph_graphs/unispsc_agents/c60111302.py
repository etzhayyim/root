from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_details: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: ProcurementState):
    details = state['item_details']
    errors = []
    if not details.get('material'): errors.append('Missing material spec')
    if not details.get('size'): errors.append('Missing letter size')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
