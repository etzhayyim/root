from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralFuelState(TypedDict):
    batch_id: str
    gravity_index: float
    sulfur_pct: float
    status: str
    logs: List[str]

def validate_quality(state: MineralFuelState) -> MineralFuelState:
    if state['sulfur_pct'] > 0.5:
        state['status'] = 'REJECTED'
        state['logs'].append('High sulfur content detected')
    else:
        state['status'] = 'CERTIFIED'
    return state

def check_sanctions(state: MineralFuelState) -> MineralFuelState:
    if state['status'] != 'REJECTED':
        state['status'] = 'SANCTION_CLEAR'
    return state

builder = StateGraph(MineralFuelState)
builder.add_node('validate', validate_quality)
builder.add_node('sanctions', check_sanctions)
builder.set_entry_point('validate')
builder.add_edge('validate', 'sanctions')
builder.add_edge('sanctions', END)
graph = builder.compile()