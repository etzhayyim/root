from typing import TypedDict
from langgraph.graph import StateGraph, END

class BindingProcurementState(TypedDict):
    quantity: int
    binding_type: str
    is_compatible: bool

def validate_compatibility(state: BindingProcurementState):
    # Business logic for verifying binding kit compatibility
    state['is_compatible'] = state['binding_type'] in ['wire', 'comb', 'coil']
    return state

def approve_order(state: BindingProcurementState):
    return {'status': 'approved' if state['is_compatible'] else 'rejected'}

graph = StateGraph(BindingProcurementState)
graph.add_node('validate', validate_compatibility)
graph.add_node('approve', approve_order)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()