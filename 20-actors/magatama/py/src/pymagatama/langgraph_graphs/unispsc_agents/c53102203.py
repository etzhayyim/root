from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClothingState(TypedDict):
    item_id: str
    fabric_approved: bool
    authenticity_check: bool

def validate_materials(state: ClothingState) -> ClothingState:
    print(f'Checking {state["item_id"]} for fabric compliance...')
    state['fabric_approved'] = True
    return state

def check_authenticity(state: ClothingState) -> ClothingState:
    print(f'Verifying patterns for {state["item_id"]}...')
    state['authenticity_check'] = True
    return state

graph = StateGraph(ClothingState)
graph.add_node('material_validation', validate_materials)
graph.add_node('authenticity_verification', check_authenticity)
graph.set_entry_point('material_validation')
graph.add_edge('material_validation', 'authenticity_verification')
graph.add_edge('authenticity_verification', END)
graph = graph.compile()