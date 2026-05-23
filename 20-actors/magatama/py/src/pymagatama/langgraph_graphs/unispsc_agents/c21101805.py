from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorProcurementState(TypedDict):
    engine_power: float
    has_safety_certification: bool
    maintenance_records_verified: bool
    approval_status: str

def validate_specs(state: TractorProcurementState):
    if state['engine_power'] > 0 and state['has_safety_certification']:
        return {'approval_status': 'COMPLIANT'}
    return {'approval_status': 'PENDING_REVIEW'}

def check_history(state: TractorProcurementState):
    if state['maintenance_records_verified']:
        return {'approval_status': 'APPROVED'}
    return {'approval_status': 'REJECTED'}

graph = StateGraph(TractorProcurementState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_history', check_history)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_history')
graph.add_edge('check_history', END)
graph = graph.compile()
