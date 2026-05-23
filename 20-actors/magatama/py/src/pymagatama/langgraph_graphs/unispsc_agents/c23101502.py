from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    payload: float
    compatibility_check: bool
    compliant: bool

def validate_spec(state: RobotState):
    state['compliant'] = state['payload'] > 0 and state['compatibility_check']
    return state

builder = StateGraph(RobotState)
builder.add_node('validate', validate_spec)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
