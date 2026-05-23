from typing import TypedDict
from langgraph.graph import StateGraph, END

class NucleicAcidState(TypedDict):
    purity: float
    dnase_free: bool
    is_compliant: bool

def validate_purity(state: NucleicAcidState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['dnase_free']
    return state

graph = StateGraph(NucleicAcidState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
