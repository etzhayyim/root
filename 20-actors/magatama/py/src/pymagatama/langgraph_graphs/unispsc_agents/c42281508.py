from typing import TypedDict
from langgraph.graph import StateGraph, END

class AutoclaveState(TypedDict):
    capacity: float
    safety_verified: bool
    compliant: bool

def validate_specs(state: AutoclaveState):
    state['safety_verified'] = state['capacity'] > 0
    return state

def check_compliance(state: AutoclaveState):
    state['compliant'] = state['safety_verified']
    return state

graph = StateGraph(AutoclaveState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
