from typing import TypedDict
from langgraph.graph import StateGraph, END

class CartProcurementState(TypedDict):
    capacity_kg: float
    material_type: str
    is_compliant: bool

def validate_specs(state: CartProcurementState):
    state['is_compliant'] = state['capacity_kg'] > 0 and len(state['material_type']) > 0
    return state

def determine_approval(state: CartProcurementState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(CartProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)