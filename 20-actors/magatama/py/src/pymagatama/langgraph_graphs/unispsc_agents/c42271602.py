from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpirometerState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    calibration_status: bool

def validate_medical_compliance(state: SpirometerState):
    print(f'Validating compliance for {state[\'device_id\']}')
    return {\'compliance_docs\': [\'ISO13485\', \'CE_Mark\']}

def perform_calibration_check(state: SpirometerState):
    print(\'Verifying sensor calibration benchmarks...\')
    return {\'calibration_status\': True}

graph = StateGraph(SpirometerState)
graph.add_node("compliance", validate_medical_compliance)
graph.add_node("calibration", perform_calibration_check)
graph.add_edge("compliance", "calibration")
graph.add_edge("calibration", END)
graph.set_entry_point("compliance")
graph = graph.compile()