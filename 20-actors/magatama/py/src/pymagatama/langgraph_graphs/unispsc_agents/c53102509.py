from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GarterState(TypedDict):
    material: str
    elasticity: float
    compliance_docs: List[str]
    approved: bool

def validate_material(state: GarterState):
    # Business logic for textile safety validation
    is_safe = state['material'] in ['Nylon', 'Polyester', 'Spandex']
    return {'approved': is_safe}

def check_elasticity(state: GarterState):
    # Logic for verifying elasticity thresholds
    is_quality = state['elasticity'] > 0.8
    return {'approved': state['approved'] and is_quality}

graph = StateGraph(GarterState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_elasticity', check_elasticity)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_elasticity')
graph.add_edge('check_elasticity', END)
