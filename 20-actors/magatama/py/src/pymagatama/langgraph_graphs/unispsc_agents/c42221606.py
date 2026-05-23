from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubingProcurementState(TypedDict):
    material_compliance: bool
    sterilization_cert: bool
    is_approved: bool

def validate_compliance(state: TubingProcurementState):
    state['is_approved'] = state['material_compliance'] and state['sterilization_cert']
    return state

def route_by_compliance(state: TubingProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(TubingProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_conditional_edges('validate', route_by_compliance, {'approved': END, 'rejected': END})
graph.set_entry_point('validate')
graph = graph.compile()
