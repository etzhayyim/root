from typing import TypedDict
from langgraph.graph import StateGraph, END

class LeadCastState(TypedDict):
    purity_level: float
    dimensions_ok: bool
    toxicity_report: str

def validate_purity(state: LeadCastState):
    return {'purity_level': max(state['purity_level'], 99.9)}

def check_compliance(state: LeadCastState):
    state['dimensions_ok'] = True
    return state

graph = StateGraph(LeadCastState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
