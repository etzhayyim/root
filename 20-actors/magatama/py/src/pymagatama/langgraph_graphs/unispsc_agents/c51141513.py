from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity_level: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: PharmState):
    return {'is_approved': state['purity_level'] >= 99.0 and state['compliance_docs']}

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()