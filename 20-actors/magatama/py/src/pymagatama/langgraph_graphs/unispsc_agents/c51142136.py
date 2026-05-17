from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlurbiprofenState(TypedDict):
    purity: float
    gmp_verified: bool
    safety_check: bool

def validate_purity(state: FlurbiprofenState):
    return {'purity': state['purity'] >= 99.0}

def verify_compliance(state: FlurbiprofenState):
    return {'gmp_verified': True}

graph = StateGraph(FlurbiprofenState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', verify_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()