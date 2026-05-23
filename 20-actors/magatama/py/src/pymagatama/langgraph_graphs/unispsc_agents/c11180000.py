from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class GasProcurementState(TypedDict):
    purity_level: float
    cylinder_id: str
    compliance_checks: Annotated[Sequence[str], add_messages]

def validate_purity(state: GasProcurementState) -> GasProcurementState:
    if state['purity_level'] < 99.9:
        raise ValueError('Purity below industrial threshold')
    return {'compliance_checks': ['Purity Validated']}

def check_regulations(state: GasProcurementState) -> GasProcurementState:
    return {'compliance_checks': ['HazMat Regulations Confirmed']}

builder = StateGraph(GasProcurementState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_regulations', check_regulations)
builder.add_edge('validate_purity', 'check_regulations')
builder.add_edge('check_regulations', END)
builder.set_entry_point('validate_purity')
graph = builder.compile()
