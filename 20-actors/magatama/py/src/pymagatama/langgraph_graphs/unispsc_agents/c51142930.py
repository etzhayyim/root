from typing import TypedDict
from langgraph.graph import StateGraph, END

class EtherState(TypedDict):
    purity: float
    has_msds: bool
    is_explosive_stabilized: bool
    approved: bool

def validate_ether_spec(state: EtherState):
    state['approved'] = state['purity'] >= 99.0 and state['has_msds'] and state['is_explosive_stabilized']
    return state

graph = StateGraph(EtherState)
graph.add_node('validate', validate_ether_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
