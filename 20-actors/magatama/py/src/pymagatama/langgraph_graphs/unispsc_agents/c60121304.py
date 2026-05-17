from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArtistKnifeState(TypedDict):
    blade_type: str
    blade_count: int
    safety_check: bool

def validate_safety(state: ArtistKnifeState) -> ArtistKnifeState:
    state['safety_check'] = state['blade_count'] > 0
    return state

def approve_procurement(state: ArtistKnifeState) -> ArtistKnifeState:
    print(f'Processing {state['blade_type']} procurement')
    return state

graph = StateGraph(ArtistKnifeState)
graph.add_node('safety', validate_safety)
graph.add_node('approval', approve_procurement)
graph.add_edge('safety', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('safety')
graph = graph.compile()