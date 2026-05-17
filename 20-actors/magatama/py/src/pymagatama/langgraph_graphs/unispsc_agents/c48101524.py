from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteamState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: SteamState):
    required = ['power-source', 'capacity-liters']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

graph = StateGraph(SteamState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()