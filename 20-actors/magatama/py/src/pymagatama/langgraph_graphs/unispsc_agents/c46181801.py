from typing import TypedDict
from langgraph.graph import StateGraph, END

class EyewearCaseState(TypedDict):
    material: str
    dimensions: dict
    is_compliant: bool

def validate_material(state: EyewearCaseState):
    state['is_compliant'] = state['material'] in ['leather', 'hard_plastic', 'microfiber']
    return state

def check_dimensions(state: EyewearCaseState):
    if state['dimensions'].get('length', 0) > 20:
        state['is_compliant'] = False
    return state

graph = StateGraph(EyewearCaseState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
