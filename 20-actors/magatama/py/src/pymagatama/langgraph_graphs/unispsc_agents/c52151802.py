from typing import TypedDict
from langgraph.graph import StateGraph, END

class PanState(TypedDict):
    material: str
    is_induction_compatible: bool
    safety_rating: str

def validate_materials(state: PanState) -> PanState:
    if 'lead' in state['material'].lower():
        raise ValueError('Material toxicity check failed')
    return state

def check_compatibility(state: PanState) -> PanState:
    print(f'Checking compatibility for: {state}')
    return state

graph = StateGraph(PanState)
graph.add_node('validate', validate_materials)
graph.add_node('compatible', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatible')
graph.add_edge('compatible', END)
graph = graph.compile()