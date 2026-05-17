from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    gmp_valid: bool
    compliance_check: bool

def validate_purity(state: PharmaState):
    return {'compliance_check': state['purity'] >= 99.0}

def check_gmp(state: PharmaState):
    return {'gmp_valid': True}

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_purity)
graph.add_node('gmp', check_gmp)
graph.set_entry_point('validate')
graph.add_edge('validate', 'gmp')
graph.add_edge('gmp', END)
graph = graph.compile()