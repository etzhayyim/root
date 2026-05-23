from typing import TypedDict
from langgraph.graph import StateGraph, END

class AccessFloorState(TypedDict):
    load_capacity: float
    fire_rating: str
    material_compliance: bool

def validate_load(state: AccessFloorState):
    if state['load_capacity'] < 5.0:
        raise ValueError('Insufficient load capacity for server room.')
    return 'validated'

def check_fire_code(state: AccessFloorState):
    return 'compliant' if state['fire_rating'] == 'Class A' else 'non-compliant'

graph = StateGraph(AccessFloorState)
graph.add_node('load_check', validate_load)
graph.add_node('fire_check', check_fire_code)
graph.add_edge('load_check', 'fire_check')
graph.add_edge('fire_check', END)
graph.set_entry_point('load_check')
graph = graph.compile()
