from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalProcessorState(TypedDict):
    device_id: str
    compliance_checked: bool
    calibration_status: str

def validate_compliance(state: DentalProcessorState):
    print(f'Validating compliance for {state["device_id"]}')
    return {'compliance_checked': True}

def run_calibration(state: DentalProcessorState):
    return {'calibration_status': 'CALIBRATED'}

graph = StateGraph(DentalProcessorState)
graph.add_node('validate', validate_compliance)
graph.add_node('calibrate', run_calibration)
graph.add_edge('validate', 'calibrate')
graph.set_entry_point('validate')
graph.add_edge('calibrate', END)
compile_graph = graph.compile()
