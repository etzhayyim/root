from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CoalProcurementState(TypedDict):
    spec_data: dict
    inspection_result: bool
    approval_status: str

def validate_coal_quality(state: CoalProcurementState) -> CoalProcurementState:
    spec = state['spec_data']
    # Example logic: ash content check
    is_valid = spec.get('ash_content_percent', 100) < 15.0
    return {'inspection_result': is_valid}

def process_approval(state: CoalProcurementState) -> CoalProcurementState:
    if state.get('inspection_result'):
        return {'approval_status': 'APPROVED'}
    return {'approval_status': 'REJECTED_QUALITY_FAIL'}

graph = StateGraph(CoalProcurementState)
graph.add_node('validate', validate_coal_quality)
graph.add_node('approve', process_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
