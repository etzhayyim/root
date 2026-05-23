from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SealProcurementState(TypedDict):
    part_number: str
    material_spec: str
    pressure_rating: float
    validation_status: str
    approval_path: str

def validate_specs(state: SealProcurementState):
    # Simulate engineering validation for seal specs
    if state['pressure_rating'] > 50.0:
        return {'validation_status': 'APPROVED', 'approval_path': 'FAST_TRACK'}
    return {'validation_status': 'PENDING_REVIEW', 'approval_path': 'ENGINEERING_AUDIT'}

def perform_quality_check(state: SealProcurementState):
    return {'validation_status': 'QUALITY_VERIFIED'}

graph = StateGraph(SealProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('quality_check', perform_quality_check)
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
