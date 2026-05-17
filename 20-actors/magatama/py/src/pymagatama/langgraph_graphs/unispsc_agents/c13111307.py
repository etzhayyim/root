from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_code: str
    purity_validated: bool
    safety_cleared: bool
    compliance_report: List[str]

def validate_purity(state: ProcurementState) -> ProcurementState:
    # Implement specialized chemical purity validation logic
    state['purity_validated'] = True
    state['compliance_report'].append('Purity Check Passed')
    return state

def check_safety(state: ProcurementState) -> ProcurementState:
    # Implement safety and dangerous goods protocol checks
    state['safety_cleared'] = True
    state['compliance_report'].append('Safety Protocol Cleared')
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_safety', check_safety)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_safety')
builder.add_edge('check_safety', END)
graph = builder.compile()