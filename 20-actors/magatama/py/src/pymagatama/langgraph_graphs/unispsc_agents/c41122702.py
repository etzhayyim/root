from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    material_type: str
    width: float
    compatibility_check: bool

def validate_specs(state: TapeState):
    state['compatibility_check'] = state['width'] > 0
    return state

def check_material(state: TapeState):
    print(f"Processing material: {state['material_type']}")
    return state

graph = StateGraph(TapeState)
graph.add_node("validate", validate_specs)
graph.add_node("material", check_material)
graph.add_edge("validate", "material")
graph.add_edge("material", END)
graph.set_entry_point("validate")
graph.compile()