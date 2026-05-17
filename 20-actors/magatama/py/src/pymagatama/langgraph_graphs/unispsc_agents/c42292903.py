from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_id: str
    material_compliance: bool
    sterilization_validated: bool
    final_approval: bool

def check_material(state: SurgicalDeviceState):
    print(f'Validating material specs for {state[\'device_id\']}')
    return {'material_compliance': True}

def check_sterilization(state: SurgicalDeviceState):
    print('Verifying sterilization protocols')
    return {'sterilization_validated': True}

def approve_device(state: SurgicalDeviceState):
    is_ready = state['material_compliance'] and state['sterilization_validated']
    return {'final_approval': is_ready}

graph = StateGraph(SurgicalDeviceState)
graph.add_node('material_check', check_material)
graph.add_node('sterilization_check', check_sterilization)
graph.add_node('approval', approve_device)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'sterilization_check')
graph.add_edge('sterilization_check', 'approval')
graph.add_edge('approval', END)
graphics = graph.compile()