from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    specifications: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_specs(state: ProcurementState):
    errors = []
    if 'material' not in state['specifications']: errors.append('Missing material specs')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

def route_verification(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()