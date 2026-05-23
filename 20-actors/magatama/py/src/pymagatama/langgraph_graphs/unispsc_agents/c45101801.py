from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
class CreasingMachineState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool
def validate_specs(state: CreasingMachineState):
    errors = []
    if state['spec_data'].get('max_width', 0) < 300:
        errors.append('Invalid width capacity')
    return {'validation_errors': errors}
def approve_order(state: CreasingMachineState):
    return {'is_approved': len(state['validation_errors']) == 0}
graph = StateGraph(CreasingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
