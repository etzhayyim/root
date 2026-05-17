from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GearState(TypedDict):
    gear_ratio: float
    torque: float
    validation_passed: bool
    error_logs: List[str]

def validate_gear_specs(state: GearState):
    passed = state['gear_ratio'] > 0 and state['torque'] > 0
    return {'validation_passed': passed, 'error_logs': [] if passed else ['Invalid gear specifications']}

def compute_transmission_efficiency(state: GearState):
    # Simulate efficiency calculation
    return {'torque': state['torque'] * 0.98}

graph = StateGraph(GearState)
graph.add_node('validate', validate_gear_specs)
graph.add_node('compute', compute_transmission_efficiency)
graph.add_edge('validate', 'compute')
graph.add_edge('compute', END)
graph.set_entry_point('validate')
graph = graph.compile()