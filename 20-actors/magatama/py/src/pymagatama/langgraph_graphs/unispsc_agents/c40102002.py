from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoilerState(TypedDict):
    pressure_rating: float
    safety_checked: bool

def validate_pressure(state: BoilerState):
    state['safety_checked'] = state['pressure_rating'] > 0
    return state

builder = StateGraph(BoilerState)
builder.add_node('validate', validate_pressure)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
