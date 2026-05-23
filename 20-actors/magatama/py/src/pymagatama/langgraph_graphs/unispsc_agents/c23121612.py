from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_tags: list

def validate_specs(state: RobotState):
    state['validation_passed'] = state['spec_data'].get('payload', 0) > 0
    return state

def check_compliance(state: RobotState):
    state['compliance_tags'] = ['ISO_10218'] if state['validation_passed'] else []
    return state

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
