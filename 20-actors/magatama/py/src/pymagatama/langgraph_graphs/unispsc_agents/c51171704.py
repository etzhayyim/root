from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    has_coa: bool
    is_approved: bool

def validate_quality(state: ProcurementState) -> dict:
    isValid = (state['purity_level'] >= 99.0) and state['has_coa']
    return {'is_approved': isValid}

workflow = StateGraph(ProcurementState)
workflow.add_node('validation', validate_quality)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
