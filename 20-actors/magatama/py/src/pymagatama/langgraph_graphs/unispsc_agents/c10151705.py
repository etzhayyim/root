from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class MiningState(TypedDict):
    material_id: str
    purity_level: float
    inspection_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_purity(state: MiningState) -> MiningState:
    # Logic for purity check
    state['is_compliant'] = state['purity_level'] > 0.65
    state['inspection_logs'] = [f'Purity check result: {state["purity_level"]}']
    return state

def check_logistics(state: MiningState) -> MiningState:
    if state['is_compliant']:
        state['inspection_logs'] = ['Logistics optimized for mining site transport.']
    else:
        state['inspection_logs'] = ['Logistics hold due to quality failure.']
    return state

builder = StateGraph(MiningState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_logistics', check_logistics)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_logistics')
builder.add_edge('check_logistics', END)
graph = builder.compile()