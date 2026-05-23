from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShoeCoverState(TypedDict):
    material: str
    is_anti_static: bool
    clean_room_grade: str
    approved: bool

def validate_material(state: ShoeCoverState):
    # Business logic for compliance validation
    state['approved'] = state['material'] in ['PP-Spunbond', 'PE-Coated']
    return state

def check_esd_compliance(state: ShoeCoverState):
    if state['is_anti_static'] and not state['clean_room_grade']:
        state['approved'] = False
    return state

graph = StateGraph(ShoeCoverState)
graph.add_node('validate', validate_material)
graph.add_node('esd_check', check_esd_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'esd_check')
graph.add_edge('esd_check', END)
graph = graph.compile()
