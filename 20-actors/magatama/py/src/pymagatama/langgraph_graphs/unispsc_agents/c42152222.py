from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    crucible_type: str
    material_certified: bool
    thermal_rating: float
    validation_passed: bool

def validate_material(state: DentalState):
    return {'material_certified': state['material_certified']}

def check_thermal_tolerance(state: DentalState):
    passed = state['thermal_rating'] >= 1500
    return {'validation_passed': passed}

graph = StateGraph(DentalState)
graph.add_node('check_material', validate_material)
graph.add_node('check_thermal', check_thermal_tolerance)
graph.set_entry_point('check_material')
graph.add_edge('check_material', 'check_thermal')
graph.add_edge('check_thermal', END)
compile_graph = graph.compile()