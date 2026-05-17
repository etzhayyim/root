from langgraph.graph import StateGraph, END
from typing import TypedDict

class PlumbingState(TypedDict):
    part_number: str
    flow_gpm: float
    material_certified: bool
    approved: bool

def validate_specs(state: PlumbingState):
    state['approved'] = state['flow_gpm'] <= 2.5 and state['material_certified']
    return state

builder = StateGraph(PlumbingState)
builder.add_node('validation', validate_specs)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()