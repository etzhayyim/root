from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    purity_check: float
    origin_verified: bool
    compliance_risk: Sequence[str]
    status: str

def validate_purity(state: MineralProcurementState) -> MineralProcurementState:
    if state['purity_check'] < 95.0:
        state['status'] = 'REJECTED_LOW_PURITY'
    return state

def check_compliance(state: MineralProcurementState) -> MineralProcurementState:
    if not state['origin_verified']:
        state['compliance_risk'] = ['sanctions-check-failed']
        state['status'] = 'PENDING_AUDIT'
    return state

builder = StateGraph(MineralProcurementState)
builder.add_node('purity_step', validate_purity)
builder.add_node('compliance_step', check_compliance)
builder.set_entry_point('purity_step')
builder.add_edge('purity_step', 'compliance_step')
builder.add_edge('compliance_step', END)
graph = builder.compile()
