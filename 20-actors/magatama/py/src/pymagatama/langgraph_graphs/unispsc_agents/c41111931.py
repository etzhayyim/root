from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlowSensorState(TypedDict):
    sensor_model: str
    spec_compliance: bool
    calibration_needed: bool

def validate_specs(state: FlowSensorState):
    # Simulate CAD/Spec validation for industrial flow sensors
    print(f"Validating specs for {state['sensor_model']}...")
    return {'spec_compliance': True}

def process_calibration(state: FlowSensorState):
    if state.get('calibration_needed'):
        print("Scheduling ISO-17025 calibration...")
    return {'calibration_needed': False}

graph = StateGraph(FlowSensorState)
graph.add_node("validate", validate_specs)
graph.add_node("calibrate", process_calibration)
graph.add_edge("validate", "calibrate")
graph.add_edge("calibrate", END)
graph.set_entry_point("validate")
graph = graph.compile()