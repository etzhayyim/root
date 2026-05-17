from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    material: str
    load_capacity: float
    dimensions: dict
    is_compliant: bool

def validate_load_capacity(state: ContainerState):
    if state['load_capacity'] > 0:
        return {'is_compliant': True}
    return {'is_compliant': False}

def check_material(state: ContainerState):
    allowed_materials = ['plastic', 'resin', 'wood']
    return {'is_compliant': state['material'] in allowed_materials}

graph = StateGraph(ContainerState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_material', check_material)
graph.set_entry_point('check_material')
graph.add_edge('check_material', 'validate_load')
graph.add_edge('validate_load', END)
graph = graph.compile()