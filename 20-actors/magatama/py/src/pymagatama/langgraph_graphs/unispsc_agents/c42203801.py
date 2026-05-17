from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_medical_grade(state: ProcurementState):
    # Business logic for CT aid verification
    state['validation_passed'] = 'ISO-10993' in state['compliance_docs']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_medical_grade)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()