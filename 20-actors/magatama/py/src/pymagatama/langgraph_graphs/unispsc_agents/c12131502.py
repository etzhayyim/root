from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ChemicalState(TypedDict):
    commodity_code: str
    purity_check: bool
    safety_clearance: bool
    logistics_status: List[str]

def validate_purity(state: ChemicalState) -> ChemicalState:
    # Simulate high-purity chemical validation logic
    state['purity_check'] = True
    return state

def check_safety(state: ChemicalState) -> ChemicalState:
    # Simulate dangerous goods compliance check
    state['safety_clearance'] = True
    return state

def update_logistics(state: ChemicalState) -> ChemicalState:
    state['logistics_status'].append('ready_for_secure_transport')
    return state

builder = StateGraph(ChemicalState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_safety', check_safety)
builder.add_node('update_logistics', update_logistics)
builder.add_edge('validate_purity', 'check_safety')
builder.add_edge('check_safety', 'update_logistics')
builder.add_edge('update_logistics', END)
builder.set_entry_point('validate_purity')
graph = builder.compile()
