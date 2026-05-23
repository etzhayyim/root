from typing import TypedDict
from langgraph.graph import StateGraph, END

class WhistleState(TypedDict):
    material: str
    decibel_rating: int
    is_compliant: bool

def validate_specs(state: WhistleState):
    state['is_compliant'] = state['decibel_rating'] >= 90 and state['material'] != 'lead'
    return state

graph = StateGraph(WhistleState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
