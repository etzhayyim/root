from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_score: float
    compliance_flag: bool

def validate_specs(state: RobotState):
    # Business logic for industrial robot compliance
    payload = state['spec_data'].get('payload_capacity_kg', 0)
    state['validation_score'] = 1.0 if payload > 0 else 0.0
    return {'validation_score': state['validation_score']}

def check_compliance(state: RobotState):
    state['compliance_flag'] = state['validation_score'] >= 0.8
    return {'compliance_flag': state['compliance_flag']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()