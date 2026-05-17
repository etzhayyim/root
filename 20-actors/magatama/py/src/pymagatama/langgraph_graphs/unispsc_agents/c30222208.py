from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlatformState(TypedDict):
    specs: dict
    validation_passed: bool
    risk_level: str

def validate_structural_specs(state: PlatformState):
    state['validation_passed'] = 'structural_integrity_cert' in state['specs']
    return state

def assess_risk(state: PlatformState):
    state['risk_level'] = 'high' if state['validation_passed'] else 'critical'
    return state

graph = StateGraph(PlatformState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('assess', assess_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assess')
graph.add_edge('assess', END)
graph = graph.compile()