from typing import TypedDict
from langgraph.graph import StateGraph, END

class DockPlateState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_status: str

def validate_load_capacity(state: DockPlateState):
    capacity = state['spec_data'].get('load_capacity_tons', 0)
    return {'validation_passed': capacity >= 1.0}

def check_safety_compliance(state: DockPlateState):
    compliance = 'pass' if state['validation_passed'] else 'fail'
    return {'compliance_status': compliance}

graph = StateGraph(DockPlateState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_safety_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()