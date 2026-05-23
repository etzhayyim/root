from typing import TypedDict
from langgraph.graph import StateGraph, END

class AstemizoleState(TypedDict):
    purity_level: float
    has_gmp_cert: bool
    compliant: bool

def validate_compliance(state: AstemizoleState):
    state['compliant'] = state['purity_level'] >= 99.0 and state['has_gmp_cert']
    return state

graph = StateGraph(AstemizoleState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
