from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArtMaterialState(TypedDict):
    material_name: str
    toxicity_compliance: bool
    color_palette: list
    is_approved: bool

def validate_materials(state: ArtMaterialState):
    # Business logic for chalk pastel certification
    state['is_approved'] = state['toxicity_compliance'] and len(state['color_palette']) > 0
    return state

builder = StateGraph(ArtMaterialState)
builder.add_node('validate', validate_materials)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
