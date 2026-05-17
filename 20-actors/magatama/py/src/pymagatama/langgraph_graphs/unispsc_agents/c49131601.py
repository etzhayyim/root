from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class AnimalCallState(TypedDict):
    spec_content: str
    validation_score: float
    approved: bool

def validate_acoustic_specs(state: AnimalCallState):
    # Simulate validation logic for animal call frequency and material
    score = 0.95 if 'dB' in state['spec_content'] else 0.5
    return {'validation_score': score, 'approved': score > 0.8}

builder = StateGraph(AnimalCallState)
builder.add_node('validate', validate_acoustic_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()