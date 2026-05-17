from langgraph.graph import StateGraph, END
from typing import TypedDict
class CylinderSpecState(TypedDict):
    material: str
    pressure_rating: float
    specs_validated: bool
def validate_materials(state: CylinderSpecState):
    return {'specs_validated': state['material'].upper() in ['ALUMINUM', 'STEEL', 'BRASS']}
def check_pressure(state: CylinderSpecState):
    return {'specs_validated': state['pressure_rating'] > 0}
graph = StateGraph(CylinderSpecState)
graph.add_node('validate_material', validate_materials)
graph.add_node('check_pressure', check_pressure)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_pressure')
graph.add_edge('check_pressure', END)
graph = graph.compile()