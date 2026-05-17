from typing import TypedDict
from langgraph.graph import StateGraph, END

class CiclopiroxState(TypedDict):
    purity_level: float
    gmp_valid: bool
    compliant: bool

def validate_quality(state: CiclopiroxState):
    state['compliant'] = state['purity_level'] >= 99.0 and state['gmp_valid']
    return state

def check_compliance(state: CiclopiroxState):
    return 'compliant' if state['compliant'] else 'non_compliant'

graph = StateGraph(CiclopiroxState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()