from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CoffeeState(TypedDict):
    origin: str
    quality_score: float
    shelf_life_ok: bool

def validate_origin(state: CoffeeState):
    if state['origin'] in ['Ethiopia', 'Colombia', 'Brazil']:
        return {'quality_score': 0.9}
    return {'quality_score': 0.5}

def check_shelf_life(state: CoffeeState):
    return {'shelf_life_ok': True}

graph = StateGraph(CoffeeState)
graph.add_node('validate', validate_origin)
graph.add_node('shelf_check', check_shelf_life)
graph.set_entry_point('validate')
graph.add_edge('validate', 'shelf_check')
graph.add_edge('shelf_check', END)
graph = graph.compile()
