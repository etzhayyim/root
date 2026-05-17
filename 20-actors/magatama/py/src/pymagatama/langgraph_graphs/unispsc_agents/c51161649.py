from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    api_name: str
    purity_level: float
    compliance_docs: bool
    is_verified: bool

def validate_purity(state: PharmState):
    state['is_verified'] = state['purity_level'] >= 99.0 and state['compliance_docs']
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()