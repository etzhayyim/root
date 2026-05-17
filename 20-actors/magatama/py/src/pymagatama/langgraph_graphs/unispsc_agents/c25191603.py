from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaunchVehicleState(TypedDict):
    technical_specs: dict
    security_clearance: bool
    is_compliant: bool

def validate_aerospace_specs(state: LaunchVehicleState):
    # Simulate CAD and Propulsion metric validation
    state['is_compliant'] = all(k in state['technical_specs'] for k in ['isp', 'thrust_to_weight'])
    return state

def security_gate(state: LaunchVehicleState):
    # Verify export controls and ITAR
    state['security_clearance'] = True
    return state

graph = StateGraph(LaunchVehicleState)
graph.add_node('validate', validate_aerospace_specs)
graph.add_node('security', security_gate)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()