from typing import TypedDict
from langgraph.graph import StateGraph, END

class RocketMotorState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str

def validate_propellant(state: RocketMotorState):
    # Simulate propellant safety verification
    state['validation_status'] = state['spec_data'].get('burn_rate') > 0
    return state

def check_compliance(state: RocketMotorState):
    # Simulate dual-use/ITAR compliance check
    state['compliance_report'] = 'ITAR_CLEARED' if state['spec_data'].get('export_license') else 'PENDING_REVIEW'
    return state

graph = StateGraph(RocketMotorState)
graph.add_node('validate', validate_propellant)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
