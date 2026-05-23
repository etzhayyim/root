from typing import TypedDict
from langgraph.graph import StateGraph, END

class SafetyGearState(TypedDict):
    nrr_rating: float
    compliance_code: str
    is_approved: bool

def validate_specs(state: SafetyGearState):
    state['is_approved'] = state['nrr_rating'] >= 20 and state['compliance_code'] != ''
    return state

graph = StateGraph(SafetyGearState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
