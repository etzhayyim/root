from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlowSwitchState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: FlowSwitchState):
    required = ['detection_range', 'fluid_type', 'pressure_rating']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: FlowSwitchState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(FlowSwitchState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
