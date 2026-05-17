from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StationeryState(TypedDict):
    material: str
    dimensions: dict
    approved: bool

def validate_holder(state: StationeryState):
    state['approved'] = state['material'] in ['metal', 'wood', 'plastic'] and state['dimensions']['height'] > 0
    return state

builder = StateGraph(StationeryState)
builder.add_node('validate', validate_holder)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()