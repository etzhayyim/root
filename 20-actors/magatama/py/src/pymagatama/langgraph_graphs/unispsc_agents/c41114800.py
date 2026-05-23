from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabState(TypedDict):
    instrument_type: str
    calibration_status: bool
    validation_error: str

def validate_instrument(state: LabState):
    print(f"Validating setup: {state['instrument_type']}")
    return {'calibration_status': True}

def process_data(state: LabState):
    print("Processing testing data...")
    return {'validation_error': None}

graph = StateGraph(LabState)
graph.add_node("validate", validate_instrument)
graph.add_node("process", process_data)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph = graph.compile()
