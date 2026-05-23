from typing import TypedDict
from langgraph.graph import StateGraph, END

class HoseState(TypedDict):
    spec: dict
    validation_log: list
    is_approved: bool

def validate_pressure_safety(state: HoseState):
    pressure = state['spec'].get('working_pressure_bar', 0)
    state['is_approved'] = pressure > 0
    state['validation_log'].append('Pressure check completed.')
    return state

def check_material_safety(state: HoseState):
    material = state['spec'].get('material_composition', 'unknown').lower()
    if 'asbestos' in material:
        state['is_approved'] = False
        state['validation_log'].append('Material safety violation.')
    return state

graph = StateGraph(HoseState)
graph.add_node('pressure_check', validate_pressure_safety)
graph.add_node('material_check', check_material_safety)
graph.set_entry_point('pressure_check')
graph.add_edge('pressure_check', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
