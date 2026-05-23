from typing import TypedDict
from langgraph.graph import StateGraph, END
class NetworkDeviceState(TypedDict):
    device_specs: dict
    validation_passed: bool
    export_control_check: bool
def validate_specs(state: NetworkDeviceState):
    required = ['Wavelength_Bandwidth', 'Transmission_Rate']
    passed = all(k in state['device_specs'] for k in required)
    return {'validation_passed': passed}
def check_compliance(state: NetworkDeviceState):
    return {'export_control_check': True}
graph = StateGraph(NetworkDeviceState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
