from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_id: str
    material_spec: str
    sterility_check: bool
    is_approved: bool

def validate_material(state: SurgicalDeviceState):
    # Perform material compliance check
    return {'material_spec': 'Medical Grade Stainless Steel Verified'}

def perform_quality_inspection(state: SurgicalDeviceState):
    # Simulate X-ray or physical tolerance verification
    return {'is_approved': True if state['sterility_check'] else False}

graph = StateGraph(SurgicalDeviceState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', perform_quality_inspection)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()
