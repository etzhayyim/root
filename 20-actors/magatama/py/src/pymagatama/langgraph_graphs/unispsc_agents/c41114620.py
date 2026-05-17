from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShockTestState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_alert: bool

def validate_specs(state: ShockTestState):
    # Logic to verify payload vs G-force limits
    passed = state['spec_data'].get('peak_acceleration_g', 0) > 0
    return {'validation_passed': passed}

def check_compliance(state: ShockTestState):
    # Dual-use export control checks
    alert = state['spec_data'].get('dual_use', False)
    return {'compliance_alert': alert}

graph = StateGraph(ShockTestState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()