from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcainamideState(TypedDict):
    purity: float
    compliance_docs: bool
    is_verified: bool

def validate_purity(state: ProcainamideState):
    state['is_verified'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcainamideState):
    state['is_verified'] = state['is_verified'] and state['compliance_docs']
    return state

graph = StateGraph(ProcainamideState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
