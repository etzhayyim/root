from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ResinProcessingState(TypedDict):
    material_id: str
    purity: float
    compliance_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ResinProcessingState):
    approved = state['purity'] >= 99.9
    return {'is_approved': approved, 'compliance_checks': ['Purity validation passed' if approved else 'Purity failed']}

def check_compliance(state: ResinProcessingState):
    return {'compliance_checks': ['Safety documentation verified']}

builder = StateGraph(ResinProcessingState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
