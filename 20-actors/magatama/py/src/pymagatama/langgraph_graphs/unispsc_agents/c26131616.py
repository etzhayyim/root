from typing import TypedDict
from langgraph.graph import StateGraph, END

class DamperState(TypedDict):
    spec_data: dict
    approved: bool

def validate_leakage(state: DamperState):
    limit = state['spec_data'].get('leakage_class', 0)
    return {'approved': limit >= 1}

def check_materials(state: DamperState):
    materials = state['spec_data'].get('materials', [])
    return {'approved': 'SUS316' in materials}

graph = StateGraph(DamperState)
graph.add_node('leakage', validate_leakage)
graph.add_node('material', check_materials)
graph.set_entry_point('leakage')
graph.add_edge('leakage', 'material')
graph.add_edge('material', END)
graph = graph.compile()
