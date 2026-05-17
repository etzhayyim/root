from typing import TypedDict
from langgraph.graph import StateGraph, END

class AccessUnitState(TypedDict):
    device_id: str
    security_compliance: bool
    throughput_mbps: int
    is_configured: bool

def validate_specs(state: AccessUnitState):
    return {'security_compliance': state['throughput_mbps'] > 0}

def configure_device(state: AccessUnitState):
    return {'is_configured': True}

graph = StateGraph(AccessUnitState)
graph.add_node('validate', validate_specs)
graph.add_node('configure', configure_device)
graph.add_edge('validate', 'configure')
graph.add_edge('configure', END)
graph.set_entry_point('validate')
graph = graph.compile()