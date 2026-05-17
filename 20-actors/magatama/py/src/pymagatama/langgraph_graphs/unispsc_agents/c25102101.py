from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VehicleProcurementState(TypedDict):
    vehicle_id: str
    specs: dict
    validation_passed: bool
    compliance_checks: List[str]

def validate_specs(state: VehicleProcurementState):
    required = ['gcwr', 'emission_standard']
    passed = all(k in state['specs'] for k in required)
    return {**state, 'validation_passed': passed}

def check_compliance(state: VehicleProcurementState):
    return {**state, 'compliance_checks': ['DOT_COMPLIANCE', 'EPA_EMISSION_LEVEL']}

graph = StateGraph(VehicleProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()