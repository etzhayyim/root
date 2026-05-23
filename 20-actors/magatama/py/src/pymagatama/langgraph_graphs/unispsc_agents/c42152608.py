from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OrthoState(TypedDict):
    part_number: str
    material_certified: bool
    sterility_verified: bool
    steps: List[str]

def validate_material(state: OrthoState):
    state['material_certified'] = True
    state['steps'].append('Material compliance validated')
    return state

def check_sterility(state: OrthoState):
    state['sterility_verified'] = True
    state['steps'].append('Sterility report verified')
    return state

graph = StateGraph(OrthoState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_sterility', check_sterility)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_sterility')
graph.add_edge('check_sterility', END)
graph = graph.compile()
