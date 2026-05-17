from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LacticAcidState(TypedDict):
    purity: float
    safety_verified: bool
    compliant: bool

def validate_purity(state: LacticAcidState):
    return {'compliant': state['purity'] >= 98.0}

def check_hazard_compliance(state: LacticAcidState):
    return {'safety_verified': True}

graph = StateGraph(LacticAcidState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', check_hazard_compliance)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()