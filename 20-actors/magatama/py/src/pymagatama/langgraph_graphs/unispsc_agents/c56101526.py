from typing import TypedDict
from langgraph.graph import StateGraph, END

class FridgeSpecState(TypedDict):
    model_number: str
    energy_rating: float
    noise_level: int
    is_compliant: bool

def validate_specs(state: FridgeSpecState):
    state['is_compliant'] = state['energy_rating'] >= 4.0 and state['noise_level'] < 30
    return state

graph = StateGraph(FridgeSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
