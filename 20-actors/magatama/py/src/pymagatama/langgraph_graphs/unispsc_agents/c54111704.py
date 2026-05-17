from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WatchStrapState(TypedDict):
    material: str
    authenticity_verified: bool
    is_compliant: bool

def validate_material(state: WatchStrapState):
    state['is_compliant'] = state['material'] in ['leather', 'silicone', 'stainless_steel']
    return state

def verify_authenticity(state: WatchStrapState):
    state['authenticity_verified'] = True
    return state

graph = StateGraph(WatchStrapState)
graph.add_node('validate', validate_material)
graph.add_node('verify', verify_authenticity)
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph.set_entry_point('validate')