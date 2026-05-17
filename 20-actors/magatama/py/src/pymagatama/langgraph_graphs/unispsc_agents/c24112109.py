from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrumState(TypedDict):
    material: str
    un_certified: bool
    capacity: float

def validate_material(state: DrumState):
    if state['material'] not in ['HDPE', 'Wood', 'Fiber']:
        return {'status': 'invalid_material'}
    return {'status': 'validated'}

def check_hazard(state: DrumState):
    if state['un_certified'] and state['capacity'] > 200:
        return {'hazard_check': 'high_risk'}
    return {'hazard_check': 'standard'}

graph = StateGraph(DrumState)
graph.add_node('validation', validate_material)
graph.add_node('hazard', check_hazard)
graph.set_entry_point('validation')
graph.add_edge('validation', 'hazard')
graph.add_edge('hazard', END)
graph = graph.compile()