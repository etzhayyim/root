from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RopeProcurementState(TypedDict):
    material: str
    diameter: float
    strength_check: bool
    is_approved: bool

def validate_material(state: RopeProcurementState):
    is_cotton = state['material'].lower() == 'cotton'
    return {'is_approved': is_cotton}

def check_strength(state: RopeProcurementState):
    strength_ok = state['diameter'] > 0
    return {'strength_check': strength_ok}

graph = StateGraph(RopeProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('strength', check_strength)
graph.set_entry_point('validate')
graph.add_edge('validate', 'strength')
graph.add_edge('strength', END)
graph = graph.compile()
