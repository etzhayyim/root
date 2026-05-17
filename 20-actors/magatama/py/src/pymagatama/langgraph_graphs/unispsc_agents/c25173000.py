from langgraph.graph import StateGraph, END
from typing import TypedDict

class LightingState(TypedDict):
    spec_requirements: dict
    validation_passed: bool

def validate_emc(state: LightingState):
    # Simulate EMC compliance check for automotive electrical components
    passed = state['spec_requirements'].get('emc_compliant', False)
    return {'validation_passed': passed}

graph = StateGraph(LightingState)
graph.add_node('validate_emc', validate_emc)
graph.set_entry_point('validate_emc')
graph.add_edge('validate_emc', END)
graph = graph.compile()