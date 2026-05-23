from typing import TypedDict
from langgraph.graph import StateGraph, END

class EstazolamState(TypedDict):
    purity_level: float
    regulatory_compliant: bool
    approved: bool

def validate_purity(state: EstazolamState):
    state['regulatory_compliant'] = state['purity_level'] >= 99.9
    return state

def check_license(state: EstazolamState):
    state['approved'] = state['regulatory_compliant']
    return state

graph = StateGraph(EstazolamState)
graph.add_node('validate', validate_purity)
graph.add_node('license', check_license)
graph.add_edge('validate', 'license')
graph.add_edge('license', END)
graph.set_entry_point('validate')
graph = graph.compile()
