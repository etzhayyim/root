from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity_level: float
    certification_valid: bool
    approved: bool

def check_purity(state: PharmState):
    state['approved'] = state['purity_level'] >= 99.5
    return {'approved': state['approved']}

def validate_docs(state: PharmState):
    return {'certification_valid': True}

graph = StateGraph(PharmState)
graph.add_node('check_purity', check_purity)
graph.add_node('validate_docs', validate_docs)
graph.set_entry_point('check_purity')
graph.add_edge('check_purity', 'validate_docs')
graph.add_edge('validate_docs', END)
graph = graph.compile()