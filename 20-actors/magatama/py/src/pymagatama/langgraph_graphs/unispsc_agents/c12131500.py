from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity_level: float
    compliance_checks: List[str]
    approved: bool

def validate_purity(state: ChemicalState):
    # Business logic for purity verification
    is_pure = state['purity_level'] >= 0.99
    return {'approved': is_pure, 'compliance_checks': state['compliance_checks'] + ['purity_validated']}

def check_regulations(state: ChemicalState):
    # Placeholder for dual-use export control checks
    return {'compliance_checks': state['compliance_checks'] + ['export_control_passed']}

builder = StateGraph(ChemicalState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_regulations)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
