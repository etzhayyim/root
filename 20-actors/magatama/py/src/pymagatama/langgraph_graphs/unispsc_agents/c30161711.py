from typing import TypedDict
from langgraph.graph import StateGraph, END

class CarpetState(TypedDict):
    material_data: dict
    compliance_check: bool

def validate_materials(state: CarpetState):
    # Simulate material spec validation
    passed = state['material_data'].get('uv_rating', 0) >= 5
    return {'compliance_check': passed}

graph = StateGraph(CarpetState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
