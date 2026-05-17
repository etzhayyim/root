from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    status: str

def validate_medical_grade(state: ProcurementState):
    # Simulate validation logic for medical tray material specs
    if 'ISO_13485' in state['compliance_docs']:
        return {'status': 'CERTIFIED'}
    return {'status': 'REJECTED'}

def process_tray_order(state: ProcurementState):
    return {'status': 'PROCESSED'}

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_medical_grade)
workflow.add_node('process', process_tray_order)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'process')
workflow.add_edge('process', END)
graph = workflow.compile()