from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ReflectorState(TypedDict):
    material: str
    reflectivity: float
    status: str

def validate_reflectivity(state: ReflectorState):
    if state['reflectivity'] < 0.90:
        return {'status': 'rejected'}
    return {'status': 'approved'}

def check_material(state: ReflectorState):
    allowed = ['Aluminum', 'Silver', 'Polished Steel']
    if state['material'] in allowed:
        return {'status': 'material_accepted'}
    return {'status': 'invalid_material'}

graph = StateGraph(ReflectorState)
graph.add_node('check_material', check_material)
graph.add_node('validate_reflectivity', validate_reflectivity)
graph.set_entry_point('check_material')
graph.add_edge('check_material', 'validate_reflectivity')
graph.add_edge('validate_reflectivity', END)
graph = graph.compile()