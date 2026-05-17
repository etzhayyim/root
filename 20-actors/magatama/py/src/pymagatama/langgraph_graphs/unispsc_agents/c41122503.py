from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BorerState(TypedDict):
    borer_id: str
    material: str
    diameter_mm: float
    inspection_passed: bool

def validate_borer_spec(state: BorerState):
    passed = state['diameter_mm'] > 0 and state['material'] == 'stainless_steel'
    return {**state, 'inspection_passed': passed}

def route_to_procurement(state: BorerState):
    return 'process_order' if state['inspection_passed'] else 'reject_order'

graph = StateGraph(BorerState)
graph.add_node('validate', validate_borer_spec)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_to_procurement, {'process_order': END, 'reject_order': END})
app = graph.compile()