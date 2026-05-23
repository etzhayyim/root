from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PressBrakeState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_safety_standards(state: PressBrakeState):
    standards = state['specs'].get('Safety Certification Standards', [])
    if not standards:
        state['validation_errors'].append('Missing safety certifications')
        state['is_compliant'] = False
    return state

def check_capacity(state: PressBrakeState):
    if state['specs'].get('Maximum Bending Force (kN)', 0) <= 0:
        state['validation_errors'].append('Invalid bending force')
        state['is_compliant'] = False
    return state

graph = StateGraph(PressBrakeState)
graph.add_node('validate_safety', validate_safety_standards)
graph.add_node('check_capacity', check_capacity)
graph.add_edge('validate_safety', 'check_capacity')
graph.add_edge('check_capacity', END)
graph.set_entry_point('validate_safety')
graph = graph.compile()
