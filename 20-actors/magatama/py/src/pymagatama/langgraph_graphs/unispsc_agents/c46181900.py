from typing import TypedDict
from langgraph.graph import StateGraph, END

class HearingProtectorState(TypedDict):
    nrr_value: float
    compliance_cert: bool
    is_approved: bool

def validate_nrr(state: HearingProtectorState):
    state['is_approved'] = state['nrr_value'] >= 20.0 and state['compliance_cert']
    return state

graph = StateGraph(HearingProtectorState)
graph.add_node('validate_nrr', validate_nrr)
graph.set_entry_point('validate_nrr')
graph.add_edge('validate_nrr', END)
graph = graph.compile()
