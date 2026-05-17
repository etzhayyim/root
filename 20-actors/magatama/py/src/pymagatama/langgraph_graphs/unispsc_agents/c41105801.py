from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OligomerState(TypedDict):
    purity: float
    safety_clearance: bool
    batch_id: str

def validate_purity(state: OligomerState):
    return {'safety_clearance': state['purity'] >= 99.0}

def storage_check(state: OligomerState):
    return {'safety_clearance': state['safety_clearance'] and True}

graph = StateGraph(OligomerState)
graph.add_node('validate', validate_purity)
graph.add_node('storage', storage_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph = graph.compile()