from typing import TypedDict
from langgraph.graph import StateGraph, END

class StarFruitState(TypedDict):
    origin: str
    brix_level: float
    inspection_passed: bool

def validate_quality(state: StarFruitState) -> dict:
    passed = state['brix_level'] >= 8.0
    return {'inspection_passed': passed}

def route_logistics(state: StarFruitState):
    return 'success' if state['inspection_passed'] else 'reject'

graph = StateGraph(StarFruitState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()