from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class BearingProcurementState(TypedDict):
    spec_id: str
    validation_score: float
    approved: bool

def validate_bearing_specs(state: BearingProcurementState):
    # Simulate CAD/Spec validation logic
    score = 0.95 if 'bearing' in state['spec_id'].lower() else 0.0
    return {'validation_score': score, 'approved': score > 0.9}

def route_procurement(state: BearingProcurementState):
    return 'approved' if state['approved'] else END

graph = StateGraph(BearingProcurementState)
graph.add_node('validate', validate_bearing_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement, {'approved': END})
graph.compile()
