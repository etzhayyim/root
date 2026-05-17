from typing import TypedDict
from langgraph.graph import StateGraph, END

class LiftgateState(TypedDict):
    load_capacity: float
    specs_verified: bool
    safety_compliant: bool

def validate_specs(state: LiftgateState):
    state['specs_verified'] = state['load_capacity'] > 0
    return state

def check_compliance(state: LiftgateState):
    state['safety_compliant'] = state['specs_verified']
    return state

graph = StateGraph(LiftgateState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()