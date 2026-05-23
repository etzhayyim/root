from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    device_id: str
    calibration_data: dict
    compliance_passed: bool

def validate_specs(state: PumpState):
    # Simulate validation logic for specialized medical hardware specs
    valid = state['calibration_data'].get('pressure_range') is not None
    return {'compliance_passed': valid}

def route_verification(state: PumpState):
    return 'passed' if state['compliance_passed'] else 'failed'

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
