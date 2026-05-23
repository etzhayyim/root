from typing import TypedDict
from langgraph.graph import StateGraph, END

class BinocularTestState(TypedDict):
    equipment_id: str
    calibration_status: bool
    compliance_docs: list
    is_approved: bool

def validate_specs(state: BinocularTestState):
    state['is_approved'] = state['calibration_status'] and len(state['compliance_docs']) > 0
    return 'approved' if state['is_approved'] else 'rejected'

workflow = StateGraph(BinocularTestState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
