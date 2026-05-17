from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlowDetectorState(TypedDict):
    device_id: str
    calibration_status: bool
    accuracy_check: float

def validate_readings(state: FlowDetectorState):
    state['accuracy_check'] = 98.5 if state['calibration_status'] else 0.0
    return state

workflow = StateGraph(FlowDetectorState)
workflow.add_node('validate', validate_readings)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()