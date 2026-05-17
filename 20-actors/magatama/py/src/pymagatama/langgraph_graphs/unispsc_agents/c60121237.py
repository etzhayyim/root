from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaletteState(TypedDict):
    material: str
    dimensions: str
    is_compliant: bool

def validate_material(state: PaletteState) -> PaletteState:
    common_materials = ['plastic', 'wood', 'ceramic', 'metal']
    state['is_compliant'] = state['material'].lower() in common_materials
    return state

def finalize_spec(state: PaletteState) -> PaletteState:
    print(f'Finalizing spec for {state}')
    return state

graph = StateGraph(PaletteState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_spec)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph.compile()