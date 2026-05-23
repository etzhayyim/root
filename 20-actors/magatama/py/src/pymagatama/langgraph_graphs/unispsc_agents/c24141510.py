from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableProtectorState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_load_capacity(state: CableProtectorState):
    capacity = state['spec_data'].get('load_capacity_tons', 0)
    valid = capacity > 0
    return {'validation_results': {'load_capacity': valid}}

def check_material_safety(state: CableProtectorState):
    material = state['spec_data'].get('material', '')
    return {'validation_results': {'material_compliant': material != 'flammable'}}

graph = StateGraph(CableProtectorState)
graph.add_node('check_load', validate_load_capacity)
graph.add_node('check_material', check_material_safety)
graph.add_edge('check_load', 'check_material')
graph.add_edge('check_material', END)
graph.set_entry_point('check_load')
graph = graph.compile()
