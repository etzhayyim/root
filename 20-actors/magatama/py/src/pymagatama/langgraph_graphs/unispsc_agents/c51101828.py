from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_name: str
    purity_level: float
    gmp_certified: bool
    approved: bool

def validate_quality(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_certified']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()