from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScoopProcurementState(TypedDict):
    material: str
    volume_ml: float
    has_food_safety_cert: bool
    approved: bool

def validate_materials(state: ScoopProcurementState):
    valid_materials = ['stainless steel', 'polypropylene', 'polycarbonate']
    return {'approved': state['material'] in valid_materials and state['has_food_safety_cert']}

def route_by_approval(state: ScoopProcurementState):
    return 'process' if state['approved'] else END

graph = StateGraph(ScoopProcurementState)
graph.add_node('validate', validate_materials)
graph.add_conditional_edges('validate', route_by_approval)
graph.set_entry_point('validate')
