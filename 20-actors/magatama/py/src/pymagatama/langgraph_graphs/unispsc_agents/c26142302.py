from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShieldingState(TypedDict):
    lead_eq: float
    purity_level: float
    verified: bool

def validate_shielding(state: ShieldingState):
    is_valid = state['lead_eq'] >= 0.5 and state['purity_level'] >= 99.9
    return {'verified': is_valid}

graph = StateGraph(ShieldingState)
graph.add_node('validate', validate_shielding)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
