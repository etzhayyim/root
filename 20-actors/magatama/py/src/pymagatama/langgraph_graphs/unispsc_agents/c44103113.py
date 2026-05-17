from typing import TypedDict
from langgraph.graph import StateGraph, END

class InkjetState(TypedDict):
    model_number: str
    yield_rating: int
    compatibility_verified: bool

def validate_compatibility(state: InkjetState) -> InkjetState:
    print(f'Validating: {state[\'model_number\']}')
    state[\'compatibility_verified\'] = True
    return state

builder = StateGraph(InkjetState)
builder.add_node('validate', validate_compatibility)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()