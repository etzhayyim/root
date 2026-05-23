from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class MiningState(TypedDict):
    depth: float
    torque: float
    is_compliant: bool

def validate_geology(state: MiningState) -> MiningState:
    state['is_compliant'] = state['depth'] > 0 and state['torque'] > 500
    return state

def execute_drilling(state: MiningState) -> MiningState:
    if state['is_compliant']:
        print(f'Drilling to {state['depth']}m with {state['torque']}Nm')
    return state

builder = StateGraph(MiningState)
builder.add_node('validate', validate_geology)
builder.add_node('drill', execute_drilling)
builder.set_entry_point('validate')
builder.add_edge('validate', 'drill')
builder.add_edge('drill', END)
graph = builder.compile()
