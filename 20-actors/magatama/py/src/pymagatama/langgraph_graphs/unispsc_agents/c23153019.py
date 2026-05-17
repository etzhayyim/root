from typing import TypedDict
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    part_number: str
    torque_check: bool
    compliance_verified: bool

def validate_specs(state: ActuatorState):
    # Simulate CAD/Spec verification logic
    state['torque_check'] = True
    return 'compliance_step'

def check_compliance(state: ActuatorState):
    # Simulate regulatory/Export check
    state['compliance_verified'] = True
    return END

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.set_entry_point('validate')
graph = graph.compile()