from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TankState(TypedDict):
    specifications: dict
    validation_results: List[str]
    approved: bool

def validate_pressure_specs(state: TankState):
    pressure = state['specifications'].get('pressure_rating_mpa', 0)
    if pressure > 1.0:
        state['validation_results'].append('High-pressure certification required.')
    return {'validation_results': state['validation_results']}

def check_material_safety(state: TankState):
    material = state['specifications'].get('material_grade', '')
    if 'SUS316' in material:
        state['validation_results'].append('Material compliant with pharma-grade.')
    return {'validation_results': state['validation_results']}

graph = StateGraph(TankState)
graph.add_node('pressure_check', validate_pressure_specs)
graph.add_node('material_check', check_material_safety)
graph.set_entry_point('pressure_check')
graph.add_edge('pressure_check', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
