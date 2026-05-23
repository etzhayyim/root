from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalDeviceState(TypedDict):
    device_id: str
    compliance_checked: bool
    sterilization_valid: bool

def validate_certification(state: MedicalDeviceState):
    print(f'Checking compliance for {state['device_id']}')
    return {'compliance_checked': True}

def verify_sterilization(state: MedicalDeviceState):
    print('Verifying sterile barrier integrity')
    return {'sterilization_valid': True}

graph = StateGraph(MedicalDeviceState)
graph.add_node('cert_check', validate_certification)
graph.add_node('sterile_check', verify_sterilization)
graph.set_entry_point('cert_check')
graph.add_edge('cert_check', 'sterile_check')
graph.add_edge('sterile_check', END)
graph = graph.compile()
