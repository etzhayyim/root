from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    powder_id: str
    purity_level: float
    particle_distribution: float
    inspection_status: str
    safety_clearance: bool

def validate_purity(state: MetalPowderState):
    is_pure = state['purity_level'] >= 99.9
    return {'inspection_status': 'PASSED' if is_pure else 'FAILED'}

def check_safety(state: MetalPowderState):
    return {'safety_clearance': state['inspection_status'] == 'PASSED'}

graph = StateGraph(MetalPowderState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()