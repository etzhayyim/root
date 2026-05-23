from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotSystemState(TypedDict):
    sensor_data: dict
    maintenance_logs: List[str]
    needs_service: bool

def validate_sensor_readings(state: RobotSystemState) -> RobotSystemState:
    # Simulate high-precision sensor validation logic
    reading = state['sensor_data'].get('value', 0)
    state['needs_service'] = reading > 95
    return state

def trigger_maintenance_workflow(state: RobotSystemState) -> RobotSystemState:
    if state['needs_service']:
        state['maintenance_logs'].append('Critical threshold reached: Maintenance required')
    return state

graph = StateGraph(RobotSystemState)
graph.add_node('validate', validate_sensor_readings)
graph.add_node('maintain', trigger_maintenance_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'maintain')
graph.add_edge('maintain', END)
graph = graph.compile()
