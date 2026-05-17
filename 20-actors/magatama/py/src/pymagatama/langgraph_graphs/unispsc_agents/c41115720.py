from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_tubing_specs(state: ProcurementState):
    errors = []
    if 'inner_diameter' not in state['specifications']:
        errors.append('Inner diameter missing')
    state['validation_errors'] = errors
    state['is_approved'] = len(errors) == 0
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_tubing_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()