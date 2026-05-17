from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material_grade: str
    capacity: float
    compliance_docs: bool
    approved: bool

def validate_material(state: KitchenwareState):
    state['approved'] = state['material_grade'] in ['304', '316']
    return state

def check_compliance(state: KitchenwareState):
    if state['approved'] and state['compliance_docs']:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_material')
graph = graph.compile()