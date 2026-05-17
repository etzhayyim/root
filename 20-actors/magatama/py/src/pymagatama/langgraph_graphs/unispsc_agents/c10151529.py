from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    commodity_code: str
    moisture_level: float
    safety_clearance: bool

def validate_moisture(state: FeedState) -> FeedState:
    if state['moisture_level'] > 14.0:
        raise ValueError('Moisture level too high for storage')
    return state

def check_safety(state: FeedState) -> FeedState:
    state['safety_clearance'] = True
    return state

builder = StateGraph(FeedState)
builder.add_node('validate', validate_moisture)
builder.add_node('safety_check', check_safety)
builder.set_entry_point('validate')
builder.add_edge('validate', 'safety_check')
builder.add_edge('safety_check', END)
graph = builder.compile()