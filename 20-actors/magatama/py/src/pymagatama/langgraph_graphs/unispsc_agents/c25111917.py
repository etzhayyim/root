from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FairleaderState(TypedDict):
    load_limit: float
    material_spec: str
    inspection_passed: bool

def validate_load_capacity(state: FairleaderState):
    state['inspection_passed'] = state['load_limit'] > 0
    return state

def check_material(state: FairleaderState):
    state['inspection_passed'] = 'Stainless' in state['material_spec']
    return state

graph = StateGraph(FairleaderState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_material', check_material)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()
