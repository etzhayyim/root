from typing import TypedDict
from langgraph.graph import StateGraph, END

class LiquidTrapState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_pressure_specs(state: LiquidTrapState):
    pressure = state['specs'].get('operating_pressure', 0)
    if pressure > 500: return {'validated': False, 'error': 'Over pressure limit'}
    return {'validated': True}

def check_material_safety(state: LiquidTrapState):
    return {'validated': state['validated']}

graph = StateGraph(LiquidTrapState)
graph.add_node('validate_pressure', validate_pressure_specs)
graph.add_node('check_material', check_material_safety)
graph.add_edge('validate_pressure', 'check_material')
graph.add_edge('check_material', END)
graph.set_entry_point('validate_pressure')
