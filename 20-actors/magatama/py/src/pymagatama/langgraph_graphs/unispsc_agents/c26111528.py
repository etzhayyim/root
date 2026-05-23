from langgraph.graph import StateGraph, END
from typing import TypedDict
import json

class HydroDriveState(TypedDict):
    pressure_spec: float
    compatibility_check: bool
    compliance_risk: str

def validate_specs(state: HydroDriveState):
    if state['pressure_spec'] > 500:
        return {'compliance_risk': 'high_pressure_overspec'}
    return {'compliance_risk': 'standard'}

def check_certification(state: HydroDriveState):
    return {'compatibility_check': True}

graph = StateGraph(HydroDriveState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()
