from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HeatExchangerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_pressure_rating(state: HeatExchangerState):
    pressure = state['spec_data'].get('pressure_rating', 0)
    if pressure <= 0:
        state['validation_errors'].append('Invalid pressure rating')
        state['is_compliant'] = False
    return state

def check_material_safety(state: HeatExchangerState):
    material = state['spec_data'].get('material', '')
    if not material:
        state['validation_errors'].append('Missing material specification')
        state['is_compliant'] = False
    return state

graph = StateGraph(HeatExchangerState)
graph.add_node('validate_pressure', validate_pressure_rating)
graph.add_node('check_material', check_material_safety)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()
