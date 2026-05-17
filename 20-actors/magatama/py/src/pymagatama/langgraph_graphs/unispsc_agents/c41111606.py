from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurveyState(TypedDict):
    device_id: str
    calibration_status: bool
    accuracy_check: float

def validate_calibration(state: SurveyState):
    return {"calibration_status": state['accuracy_check'] < 0.01}

def update_records(state: SurveyState):
    print(f"Device {state['device_id']} updated with status: {state['calibration_status']}")

graph = StateGraph(SurveyState)
graph.add_node("validate", validate_calibration)
graph.add_node("update", update_records)
graph.add_edge("validate", "update")
graph.add_edge("update", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()