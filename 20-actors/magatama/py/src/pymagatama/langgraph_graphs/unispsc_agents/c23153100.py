from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotServiceState(TypedDict):
    service_type: str
    validation_checks: List[str]
    is_compliant: bool

def validate_service(state: RobotServiceState) -> RobotServiceState:
    if state['service_type'] in ['maintenance', 'calibration']:
        state['validation_checks'].append('ISO_10218_VERIFIED')
        state['is_compliant'] = True
    return state

def integrate_system(state: RobotServiceState) -> RobotServiceState:
    if state['is_compliant']:
        state['validation_checks'].append('SYSTEM_INTEGRATION_SUCCESS')
    return state

graph = StateGraph(RobotServiceState)
graph.add_node('validate', validate_service)
graph.add_node('integrate', integrate_system)
graph.add_edge('validate', 'integrate')
graph.add_edge('integrate', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
