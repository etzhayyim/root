from typing import TypedDict
from langgraph.graph import StateGraph, END
class ResearchToolState(TypedDict):
    material: str
    volume: float
    validation_status: str
def validate_material(state: ResearchToolState):
    valid_materials = ['porcelain', 'glass', 'agate', 'stone']
    status = 'approved' if state['material'].lower() in valid_materials else 'rejected'
    return {'validation_status': status}
def check_capacity(state: ResearchToolState):
    return {'validation_status': 'approved' if state['volume'] > 0 else 'rejected'}
graph = StateGraph(ResearchToolState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_capacity', check_capacity)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_capacity')
graph.add_edge('check_capacity', END)
graph = graph.compile()
