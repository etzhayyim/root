from typing import TypedDict
from langgraph.graph import StateGraph, END

class RoofingBrushState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_materials(state: RoofingBrushState):
    materials = state['spec_data'].get('material', '')
    return {'is_compliant': 'bristle' in materials.lower()}

def prepare_order(state: RoofingBrushState):
    return {'status': 'procurement_ready'}

graph = StateGraph(RoofingBrushState)
graph.add_node('validate', validate_materials)
graph.add_node('order', prepare_order)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
graph = graph.compile()
