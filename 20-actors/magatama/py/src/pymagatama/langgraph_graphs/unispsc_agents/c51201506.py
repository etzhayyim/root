from typing import TypedDict
from langgraph.graph import StateGraph, END

class DefibrotideState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: list
    is_cleared: bool

def validate_purity(state: DefibrotideState):
    return {'is_cleared': state['purity_level'] >= 99.9}

def verify_compliance(state: DefibrotideState):
    return {'is_cleared': len(state['compliance_docs']) > 3}

graph = StateGraph(DefibrotideState)
graph.add_node('check_purity', validate_purity)
graph.add_node('check_compliance', verify_compliance)
graph.set_entry_point('check_purity')
graph.add_edge('check_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()