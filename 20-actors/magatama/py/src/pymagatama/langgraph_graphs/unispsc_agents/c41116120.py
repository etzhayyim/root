from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HematologyState(TypedDict):
    kit_id: str
    expiration_date: str
    temperature_range: str
    is_compliant: bool

def validate_supply(state: HematologyState):
    # Business logic for hematology kit validation
    state['is_compliant'] = state['expiration_date'] is not None and len(state['kit_id']) > 0
    return state

builder = StateGraph(HematologyState)
builder.add_node('validate', validate_supply)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
