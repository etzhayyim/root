from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class WeldingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    safety_checks: List[str]

def validate_specs(state: WeldingState):
    required = ['voltage', 'current', 'duty_cycle']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def perform_safety_check(state: WeldingState):
    return {'safety_checks': ['electrical_isolation', 'thermal_protection_verified']}

graph = StateGraph(WeldingState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', perform_safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
