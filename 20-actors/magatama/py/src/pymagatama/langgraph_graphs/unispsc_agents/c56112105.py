from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_ergonomics(state: FurnitureState):
    state['is_compliant'] = state['specs'].get('ergonomic_rating', 0) >= 3
    return state

def check_fire_safety(state: FurnitureState):
    if not state.get('specs', {}).get('fire_code_cert'):
        state['is_compliant'] = False
    return state

graph = StateGraph(FurnitureState)
graph.add_node('ergonomics', validate_ergonomics)
graph.add_node('safety', check_fire_safety)
graph.set_entry_point('ergonomics')
graph.add_edge('ergonomics', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()