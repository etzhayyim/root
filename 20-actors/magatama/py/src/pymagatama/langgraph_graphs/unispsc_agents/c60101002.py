from typing import TypedDict
from langgraph.graph import StateGraph, END

class MathKitState(TypedDict):
    kit_id: str
    component_count: int
    is_verified: bool

def validate_components(state: MathKitState):
    state['is_verified'] = state['component_count'] > 0
    return state

def check_durability(state: MathKitState):
    print(f'Checking durability for kit: {state['kit_id']}')
    return state

builder = StateGraph(MathKitState)
builder.add_node('validate', validate_components)
builder.add_node('durability', check_durability)
builder.set_entry_point('validate')
builder.add_edge('validate', 'durability')
builder.add_edge('durability', END)
graph = builder.compile()