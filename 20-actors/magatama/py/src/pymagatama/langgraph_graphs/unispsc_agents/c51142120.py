from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EnzymeState(TypedDict):
    purity: float
    activity_units: int
    coa_verified: bool
    passed_inspection: bool

def validate_purity(state: EnzymeState):
    state['passed_inspection'] = state['purity'] >= 99.0
    return state

def verify_coa(state: EnzymeState):
    return {'coa_verified': True} if state['activity_units'] > 2000 else {'coa_verified': False}

graph = StateGraph(EnzymeState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_coa', verify_coa)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_coa')
graph.add_edge('verify_coa', END)
app = graph.compile()