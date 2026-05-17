from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeSupplyState(TypedDict):
    item_name: str
    material: str
    is_validated: bool

def validate_material(state: OfficeSupplyState):
    valid_materials = ['plastic', 'metal', 'acrylic']
    return {'is_validated': state['material'].lower() in valid_materials}

def route_by_validation(state: OfficeSupplyState):
    return 'valid' if state['is_validated'] else 'invalid'

graph = StateGraph(OfficeSupplyState)
graph.add_node('validation', validate_material)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph.compile()