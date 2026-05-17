from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcureState(TypedDict):
    purity: float
    compliant: bool

def validate_purity(state: ProcureState):
    return {'compliant': state['purity'] >= 99.0}

def route_by_compliance(state: ProcureState):
    return 'approved' if state['compliant'] else 'rejected'

graph = StateGraph(ProcureState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'approved': END, 'rejected': END})
graph.compile()