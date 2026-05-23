from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BottleState(TypedDict):
    material: str
    is_bpa_free: bool
    safety_certs: List[str]
    validation_passed: bool

def validate_material(state: BottleState):
    state['validation_passed'] = state['is_bpa_free'] and 'BPA-free' in state['material']
    return state

def check_certs(state: BottleState):
    if len(state['safety_certs']) < 2:
        state['validation_passed'] = False
    return state

graph = StateGraph(BottleState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_certs', check_certs)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_certs')
graph.add_edge('check_certs', END)
graph = graph.compile()
