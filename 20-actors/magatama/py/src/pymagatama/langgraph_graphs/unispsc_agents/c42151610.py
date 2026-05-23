from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalToolState(TypedDict):
    tool_id: str
    material_spec: str
    is_sterile: bool
    approved: bool

def validate_material(state: DentalToolState):
    state['approved'] = state['material_spec'] == 'surgical_stainless'
    return state

def check_sterilization(state: DentalToolState):
    if state['approved']:
        state['approved'] = state['is_sterile']
    return state

graph = StateGraph(DentalToolState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_sterilization', check_sterilization)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_sterilization')
graph.add_edge('check_sterilization', END)
graph = graph.compile()
