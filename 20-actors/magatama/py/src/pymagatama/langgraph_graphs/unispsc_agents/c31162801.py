from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HandleState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_ergonomics(state: HandleState):
    errors = []
    if state['spec_data'].get('grip_diameter', 0) < 10:
        errors.append('Diameter too small for safe grip')
    return {'validation_errors': errors}

def check_material_safety(state: HandleState):
    approved_materials = ['ABS', 'Steel', 'Aluminum']
    if state['spec_data'].get('material') not in approved_materials:
        return {'is_approved': False}
    return {'is_approved': True}

graph = StateGraph(HandleState)
graph.add_node('validate_ergonomics', validate_ergonomics)
graph.add_node('check_material', check_material_safety)
graph.set_entry_point('validate_ergonomics')
graph.add_edge('validate_ergonomics', 'check_material')
graph.add_edge('check_material', END)
app = graph.compile()
