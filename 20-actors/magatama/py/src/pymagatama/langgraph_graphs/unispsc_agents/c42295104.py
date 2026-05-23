from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_id: str
    compliance_checked: bool
    sterility_verified: bool

def validate_compliance(state: SurgicalDeviceState):
    print(f'Validating compliance for {state['device_id']}')
    return {'compliance_checked': True}

def verify_sterility(state: SurgicalDeviceState):
    print('Verifying sterility documentation')
    return {'sterility_verified': True}

graph = StateGraph(SurgicalDeviceState)
graph.add_node('compliance', validate_compliance)
graph.add_node('sterility', verify_sterility)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'sterility')
graph.add_edge('sterility', END)
graph = graph.compile()
