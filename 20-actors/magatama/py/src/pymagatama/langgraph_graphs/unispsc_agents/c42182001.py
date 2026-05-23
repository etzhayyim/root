from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalDeviceState(TypedDict):
    device_id: str
    specifications: dict
    validation_passed: bool

def validate_materials(state: MedicalDeviceState):
    # Simulate material check for biocompatibility
    state['validation_passed'] = 'material' in state['specifications']
    return state

def check_certification(state: MedicalDeviceState):
    # Simulate regulatory audit
    state['validation_passed'] = state.get('validation_passed', False) and 'iso13485' in state['specifications']
    return state

graph = StateGraph(MedicalDeviceState)
graph.add_node('material_check', validate_materials)
graph.add_node('cert_check', check_certification)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()
