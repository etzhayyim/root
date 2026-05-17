from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraControlState(TypedDict):
    device_id: str
    protocol: str
    validation_status: bool

def validate_protocol(state: CameraControlState):
    state['validation_status'] = state['protocol'] in ['VISCA', 'ONVIF']
    return state

def check_compliance(state: CameraControlState):
    print(f'Checking export compliance for {state['device_id']}')
    return {'validation_status': True}

graph = StateGraph(CameraControlState)
graph.add_node('validate', validate_protocol)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()