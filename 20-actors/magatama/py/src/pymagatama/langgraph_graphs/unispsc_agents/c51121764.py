from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    drug_name: str
    purity_level: float
    has_cold_chain_cert: bool
    is_approved: bool

def validate_quality(state: PharmaState):
    state['is_approved'] = state['purity_level'] >= 99.0 and state['has_cold_chain_cert']
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compiled_graph = graph.compile()