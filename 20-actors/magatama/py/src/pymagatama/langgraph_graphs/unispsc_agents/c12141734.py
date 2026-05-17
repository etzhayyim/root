from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystProcurementState(TypedDict):
    material_id: str
    purity_level: float
    safety_check_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystProcurementState):
    is_valid = state['purity_level'] >= 99.9
    return {'safety_check_passed': is_valid, 'log': ['Purity check completed']}

def perform_safety_review(state: CatalystProcurementState):
    status = 'APPROVED' if state['safety_check_passed'] else 'REJECTED_LOW_PURITY'
    return {'log': [f'Safety review result: {status}']}

builder = StateGraph(CatalystProcurementState)
builder.add_node('validate', validate_purity)
builder.add_node('safety', perform_safety_review)
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
builder.set_entry_point('validate')
graph = builder.compile()