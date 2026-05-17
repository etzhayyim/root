from typing import TypedDict
from langgraph.graph import StateGraph, END

class HoseState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_pressure_rating(state: HoseState):
    pressure = state['spec_data'].get('pressure', 0)
    if pressure <= 0: state['validation_errors'].append('Invalid pressure rating')
    return {'validation_errors': state['validation_errors']}

def check_compliance(state: HoseState):
    is_valid = len(state['validation_errors']) == 0
    return {'is_compliant': is_valid}

graph = StateGraph(HoseState)
graph.add_node('validate_specs', validate_pressure_rating)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()