from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material: str
    thermal_rating: float
    compliant: bool

def validate_materials(state: ProcurementState):
    state['compliant'] = state['material'] == 'aluminized_polyester'
    return state

def check_thermal_specs(state: ProcurementState):
    if state['compliant']:
        state['compliant'] = state['thermal_rating'] >= 0.9
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('thermal_check', check_thermal_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'thermal_check')
graph.add_edge('thermal_check', END)
graph = graph.compile()
