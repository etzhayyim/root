from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    commodity_id: str
    purity_level: float
    safety_clearance: bool
    logistics_status: List[str]

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity_level'] < 99.5:
        state['logistics_status'].append('PURITY_REJECTED')
    else:
        state['logistics_status'].append('PURITY_VERIFIED')
    return state

def check_safety_protocols(state: ChemicalState) -> ChemicalState:
    if state['safety_clearance']:
        state['logistics_status'].append('SAFETY_APPROVED')
    else:
        state['logistics_status'].append('SAFETY_HOLD')
    return state

builder = StateGraph(ChemicalState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_safety', check_safety_protocols)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_safety')
builder.add_edge('check_safety', END)
graph = builder.compile()
