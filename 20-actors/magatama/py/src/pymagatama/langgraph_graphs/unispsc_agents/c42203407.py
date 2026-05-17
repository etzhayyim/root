from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    pressure_rating: int
    is_sterile: bool
    validation_passed: bool

def validate_pressure(state: State):
    state['validation_passed'] = state['pressure_rating'] >= 1200
    return state

def check_sterility(state: State):
    state['validation_passed'] = state['validation_passed'] and state['is_sterile']
    return state

builder = StateGraph(State)
builder.add_node('pressure_check', validate_pressure)
builder.add_node('sterility_check', check_sterility)
builder.add_edge('pressure_check', 'sterility_check')
builder.add_edge('sterility_check', END)
builder.set_entry_point('pressure_check')
graph = builder.compile()