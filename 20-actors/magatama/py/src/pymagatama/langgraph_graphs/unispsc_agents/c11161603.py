from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    raw_input: dict
    purity_check: bool
    safety_clearance: bool
    approved: bool

def validate_chemistry(state: CatalystState) -> CatalystState:
    # Logic to verify chemical purity specs
    purity = state['raw_input'].get('purity', 0)
    state['purity_check'] = purity >= 99.5
    return state

def check_safety_protocols(state: CatalystState) -> CatalystState:
    # Logic to check dangerous goods/dual-use status
    state['safety_clearance'] = True
    return state

builder = StateGraph(CatalystState)
builder.add_node('validate', validate_chemistry)
builder.add_node('safety', check_safety_protocols)
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
builder.set_entry_point('validate')
graph = builder.compile()
