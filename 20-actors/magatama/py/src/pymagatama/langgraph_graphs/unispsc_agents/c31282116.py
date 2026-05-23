from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteelComponentState(TypedDict):
    part_id: str
    specs: dict
    is_validated: bool

def validate_specs(state: SteelComponentState):
    # Custom logic for spin-formed steel component tolerance checking
    state['is_validated'] = state['specs'].get('tolerance', 0) < 0.05
    return state

def trigger_inspection(state: SteelComponentState):
    print(f'Routing part {state['part_id']} to NDT inspection facility.')
    return state

builder = StateGraph(SteelComponentState)
builder.add_node('validate', validate_specs)
builder.add_node('inspection', trigger_inspection)
builder.add_edge('validate', 'inspection')
builder.set_entry_point('validate')
builder.add_edge('inspection', END)
graph = builder.compile()
