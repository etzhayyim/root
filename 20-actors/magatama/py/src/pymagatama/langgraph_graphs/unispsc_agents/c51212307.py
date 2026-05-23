from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MetyraponeState(TypedDict):
    purity_level: float
    has_coa: bool
    compliant: bool

def validate_purity(state: MetyraponeState):
    return {'compliant': state['purity_level'] >= 99.0 and state['has_coa']}

def route_by_compliance(state: MetyraponeState):
    return 'compliant' if state['compliant'] else END

graph = StateGraph(MetyraponeState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
