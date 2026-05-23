from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_type: str
    is_sterile: bool
    validation_score: float

def validate_medical_device(state: SurgicalDeviceState):
    state['validation_score'] = 1.0 if state['is_sterile'] else 0.0
    return {'validation_score': state['validation_score']}

def process_procurement_step(state: SurgicalDeviceState):
    return {'device_type': f'verified_{state["device_type"]}'}

graph = StateGraph(SurgicalDeviceState)
graph.add_node('validate', validate_medical_device)
graph.add_node('process', process_procurement_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
