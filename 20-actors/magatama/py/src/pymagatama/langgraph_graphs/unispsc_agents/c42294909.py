from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalDeviceState(TypedDict):
    device_id: str
    pressure_specs: dict
    compliance_checked: bool

def validate_pressure(state: MedicalDeviceState):
    # Simulate validation of balloon inflation pressure rating
    state['compliance_checked'] = state['pressure_specs'].get('atm', 0) < 20
    return state

def generate_report(state: MedicalDeviceState):
    print(f"Device {state['device_id']} validation status: {state['compliance_checked']}")
    return state

graph = StateGraph(MedicalDeviceState)
graph.add_node('validate', validate_pressure)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()