from typing import TypedDict
from langgraph.graph import StateGraph, END

class BetaCounterState(TypedDict):
    spec_data: dict
    validation_passed: bool
    safety_clearance: bool

def validate_specs(state: BetaCounterState):
    # Logic to verify sensitivity and background radiation thresholds
    state['validation_passed'] = state['spec_data'].get('efficiency', 0) > 0.05
    return state

def check_compliance(state: BetaCounterState):
    # logic to cross-check export control and safety certifications
    state['safety_clearance'] = True
    return state

graph = StateGraph(BetaCounterState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()